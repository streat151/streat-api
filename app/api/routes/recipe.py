from fastapi import APIRouter, UploadFile, HTTPException, status, File

from pydantic import ValidationError

from sqlmodel import func, select

import uuid
import json
from typing import Any, Literal

from app.crud import crud_recipe
from app.models.user import Message
from app.api.deps import SessionDep, CurrentUser
from app.models.recipe.recipe import Recipe, RecipeCreate, RecipeUpdate, RecipePublic, RecipesPublic, UserRecipeSave


router = APIRouter()

"""Health check endpoint"""
@router.get("/health-check")
async def health_check():
    return "Recipes health check is good!"

"""Main recipe endpoints"""
@router.post(
    "",
    response_model=Recipe,
    status_code=status.HTTP_201_CREATED,
    description="Create a fully fleshed recipe from an uploaded JSON file and add it to the database.",
)
async def create_recipe(
    *, 
    file: UploadFile = File(..., description="JSON file containing the recipe data"),
    current_user: CurrentUser,
    session: SessionDep
) -> Recipe:
    """
    Endpoint to upload a recipe JSON file, validate it, and store it in the database.
    """
    try:
        # Read and parse the uploaded file
        contents = await file.read()
        recipe_data: dict = json.loads(contents)
        
        # Set author ID
        recipe_data['author_id'] = current_user.id
        
        # Validate the recipe data against the RecipeCreate model
        recipe_in = RecipeCreate.model_validate(recipe_data)
        
        # Create and save the recipe in the database
        db_recipe = await crud_recipe.create_recipe(session, recipe_in, file.filename)
        
        return db_recipe
    
    except json.JSONDecodeError as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON file. Please ensure the file is properly formatted."
        )
    
    except ValidationError as e:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {e}"
        )
    
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.patch("/{recipe_id}", response_model=RecipePublic)
async def edit_recipe(
    recipe_id: uuid.UUID,
    update_data: RecipeUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Create a new version of a recipe
    """
    # Get original recipe
    base_recipe = await session.get(Recipe, recipe_id)
    if not base_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Create new version
    new_version = await crud_recipe.create_recipe_version(
        session=session,
        base_recipe=base_recipe,
        update_data=update_data.model_dump(exclude_unset=True),
        current_user_id=current_user.id
    )

    return new_version


@router.get("/{recipe_id}/versions", response_model=RecipesPublic)
async def get_recipe_versions(
    recipe_id: uuid.UUID,
    session: SessionDep,
    skip: int = 0,
    limit: int = 50
) -> Any:
    """
    Get all versions of a recipe
    """
    # Find the original recipe
    root_recipe = await session.get(Recipe, recipe_id)
    if not root_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Get all versions in the version tree
    statement = (
        select(Recipe)
        .where(
            (Recipe.original_recipe_id == root_recipe.original_recipe_id) |
            (Recipe.id == root_recipe.original_recipe_id)
        )
        .order_by(Recipe.version_number.desc())
        .offset(skip)
        .limit(limit)
    )

    count_stmt = (
        select(func.count())
        .where(
            (Recipe.original_recipe_id == root_recipe.original_recipe_id) |
            (Recipe.id == root_recipe.original_recipe_id)
        )
    )

    count_result = await session.execute(count_stmt)
    versions_result = await session.execute(statement)

    return RecipesPublic(
        data=versions_result.scalars().all(),
        count=count_result.scalar()
    )


@router.get(
    "",
    response_model=RecipesPublic,
    description="Get recipes from the database with a default limit of 100 at a time",
)
async def read_recipes(
    *,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    sort: Literal["save_count", "date"] = "date"
) -> Any:
    """
    Retrieve recipes with optional sorting by save_count or created_at.
    """

    # Create and execute statement to get count of all recipes
    count_statement = select(func.count()).select_from(Recipe)
    count_result = await session.execute(count_statement)
    count = count_result.scalar()

    # Determine sorting order
    if sort == "save_count":
        order_by = Recipe.save_count.desc()
    else:
        order_by = Recipe.created_at.desc()

    # Statement to offset, limit and return recipes queried from database
    statement = select(Recipe).order_by(order_by).offset(skip).limit(limit)
    recipes_results = await session.execute(statement)
    recipes = recipes_results.scalars().all()

    return RecipesPublic(data=recipes, count=count)


@router.get("/me/saved-recipes", response_model=RecipesPublic)
async def read_saved_recipes(
    current_user: CurrentUser, 
    session: SessionDep,  
    skip: int = 0, 
    limit: int = 50
) -> Any:
    """
    Get current user's saved recipes.
    """

    # Fetch only saved recipes
    count_statement = select(func.count()).select_from(Recipe).join(UserRecipeSave).where(UserRecipeSave.user_id == current_user.id)
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


@router.delete("/{recipe_id}", response_model=Message)
async def delete_recipe(
    session: SessionDep, 
    current_user: CurrentUser, 
    recipe_id: uuid.UUID
) -> Any:
    """
    Delete a user's own recipe.
    """

    # Get queries recipe from database
    recipe = await session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Raise exception if current user does not own recipe
    if recipe.author_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Cannot delete another users's recipe."
        )
    
    # Delete, commit and return Message response
    await crud_recipe.delete_recipe(session, recipe)
    return Message(message="Recipe deleted successfully")


@router.get(
    "/search",
    response_model=RecipesPublic,
    description="Search for recipes by title with pagination.",
)
async def search_recipes(
    session: SessionDep,
    query: str,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """
    Search for recipes by title.
    """

    # Get total count of matching recipes
    count_statement = select(func.count()).where(Recipe.title.ilike(f"%{query}%"))
    count_result = await session.execute(count_statement)
    count = count_result.scalar()

    # Fetch paginated results
    statement = (
        select(Recipe)
        .where(Recipe.title.ilike(f"%{query}%"))
        .offset(skip)
        .limit(limit)
    )
    results = await session.execute(statement)
    recipes = results.scalars().all()

    return RecipesPublic(data=recipes, count=count)


@router.get("/{recipe_id}", response_model=RecipePublic | None)
async def read_recipe_by_id(
    recipe_id: uuid.UUID, session: SessionDep
) -> Any:
    """
    Get a specific recipe by id.
    """
    recipe = await session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found",
        )
    return recipe


@router.get("me/recipes", response_model=RecipesPublic)
async def read_created_recipes(
    current_user: CurrentUser, 
    session: SessionDep,  
    skip: int = 0, 
    limit: int = 50
) -> Any:
    """
    Get current user's created recipes.
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
