import uuid
from typing import Any

from fastapi import HTTPException, status

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe.recipe import Recipe, RecipeCreate


async def create_recipe(
    session: AsyncSession, 
    recipe_in: RecipeCreate, 
    filename: str
) -> Recipe:
    """
    Create a new recipe in the database.
    """
    try:
        # Convert the input model to a database model
        recipe = Recipe(**recipe_in.model_dump(), file_path=filename)
        
        # Add and commit the recipe to the database
        session.add(recipe)
        await session.commit()
        await session.refresh(recipe)
        
        return recipe
    
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recipe in the database: {str(e)}"
        )


async def delete_recipe(session: AsyncSession, recipe: Recipe) -> None:
    """
    Delete a recipe from the database.
    """
    await session.delete(recipe)
    await session.commit()


async def create_recipe_version(
    session: AsyncSession,
    base_recipe: Recipe,
    update_data: dict,
    current_user_id: uuid.UUID
) -> Recipe:
    """Create a new version of an existing recipe"""
    version_data = base_recipe.model_dump()
    version_data.update({
        "id": uuid.uuid4(),
        "version_number": base_recipe.version_number + 1,
        "previous_version_id": base_recipe.id,
        "original_recipe_id": base_recipe.original_recipe_id or base_recipe.id,
        "author_id": current_user_id,
        **update_data
    })
    
    new_version = Recipe(**version_data)
    session.add(new_version)
    await session.commit()
    await session.refresh(new_version)
    return new_version
