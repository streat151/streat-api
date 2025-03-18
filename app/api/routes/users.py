import uuid
from typing import Any, Literal

from sqlmodel import func, select
from fastapi import APIRouter, Depends, HTTPException, status

from app.crud import crud_user as crud
from app.core.config import settings
from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.models.recipe.recipe import (
    Recipe,
    RecipePublic,
    RecipesPublic,
    UserRecipeSave
)
from app.models.user import (
    Message,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)

router = APIRouter()


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
async def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """

    count_statement = select(func.count()).select_from(User)
    count_result = await session.execute(count_statement)
    count = count_result.scalar()

    statement = select(User).offset(skip).limit(limit)
    users_results = await session.execute(statement)
    users = users_results.scalars().all()

    return UsersPublic(data=users, count=count)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
async def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    user = await crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = await crud.create_user(session=session, user_create=user_in)
    return user


@router.patch("/me", response_model=UserPublic)
async def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """

    if user_in.email:
        existing_user = await crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    updated_user = await crud.update_user(session, current_user, user_in)
    return updated_user


@router.get("/me", response_model=UserPublic)
async def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.get("/me/my-recipes", response_model=RecipesPublic)
async def read_user_recipes(
    current_user: CurrentUser, 
    session: SessionDep, 
    skip: int = 0, 
    limit: int = 50
) -> Any:
    """
    Get current user's uploaded/created recipes.
    """

    # Fetch only created recipes
    count_statement = select(func.count()).select_from(Recipe).where(Recipe.author_id == current_user.id)
    statement = select(Recipe).where(Recipe.author_id == current_user.id).offset(skip).limit(limit)

    # Execute count query
    count_result = await session.execute(count_statement)
    count = count_result.scalar()

    # Execute paginated query
    results = await session.execute(statement)
    recipes = results.scalars().all()

    return RecipesPublic(data=recipes, count=count)


@router.get("/me/saved-recipes", response_model=RecipesPublic)
async def get_saved_recipes(
    current_user: CurrentUser,
    session: SessionDep,
    skip: int = 0, 
    limit: int = 50
) -> RecipesPublic:
    """
    Get a user's saved recipes.
    """
    count_statement = select(func.count()). \
            select_from(Recipe). \
            join(UserRecipeSave). \
            where(UserRecipeSave.user_id == current_user.id)
    
    statement = select(Recipe).join(UserRecipeSave).where(UserRecipeSave.user_id == current_user.id).offset(skip).limit(limit)

    # Execute count query
    count_result = await session.execute(count_statement)
    count = count_result.scalar()

    # Execute paginated query
    results = await session.execute(statement)
    recipes = results.scalars().all()

    return RecipesPublic(data=recipes, count=count)


@router.post(
    "/me/saved-recipes/{recipe_id}",
    response_model=Message,
    status_code=status.HTTP_201_CREATED,
)
async def save_recipe(
    recipe_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> Message:
    """
    Save a recipe to the current user's saved recipes.
    """
    # Verify the recipe exists
    recipe = await session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check if the recipe is already saved
    result = await session.execute(
        select(UserRecipeSave).where(
            UserRecipeSave.user_id == current_user.id,
            UserRecipeSave.recipe_id == recipe_id,
        )
    )
    existing_save = result.scalar()
    if existing_save:
        raise HTTPException(status_code=409, detail="Recipe already saved")

    # Create the save record
    save_record = UserRecipeSave(user_id=current_user.id, recipe_id=recipe_id)
    session.add(save_record)

    # Update the recipe's save count
    recipe.save_count += 1

    await session.commit()
    await session.refresh(save_record)
    return Message(message="Recipe saved successfully")


@router.delete(
    "/me/saved-recipes/{recipe_id}",
    response_model=Message,
)
async def unsave_recipe(
    recipe_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> Message:
    """
    Remove a recipe from the current user's saved recipes.
    """

    # Find the saved recipe record
    result = await session.execute(
        select(UserRecipeSave).where(
            UserRecipeSave.user_id == current_user.id,
            UserRecipeSave.recipe_id == recipe_id,
        )
    )
    save_record = result.scalar()
    if not save_record:
        raise HTTPException(status_code=404, detail="Saved recipe not found")

    # Delete the save record
    await session.delete(save_record)

    # Update the recipe's save count
    recipe = await session.get(Recipe, recipe_id)
    if recipe and recipe.save_count > 0:
        recipe.save_count -= 1

    await session.commit()
    return Message(message="Recipe unsaved successfully")


@router.delete("/me", response_model=Message)
async def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    await session.delete(current_user)
    await session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
async def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = await crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = await crud.create_user(session=session, user_create=user_create)
    return user


@router.get("/{user_id}", response_model=UserPublic | None)
async def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = await session.get(User, user_id)
    if not user:
        return None
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
async def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """

    db_user = await session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = await crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    db_user = await crud.update_user(session=session, db_user=db_user, user_in=user_in)
    return db_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
async def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    await session.delete(user)
    await session.commit()
    return Message(message="User deleted successfully")
