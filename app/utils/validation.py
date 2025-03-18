from fastapi import HTTPException

from app.models.recipe.tool import Tool
from app.models.recipe.unit import Unit
from app.models.recipe.claim import Claim
from app.models.recipe.action import Action
from app.models.recipe.recipe import Recipe
from app.models.recipe.allergen import Allergen

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession


async def validate_recipe_references(db: AsyncSession, recipe_data: dict):
    # Validate action IDs
    for step in recipe_data["steps"]:
        action_id = step["action_id"]
        result = await db.execute(select(Action).where(Action.id == action_id))
        if not result.scalars().first():
            raise HTTPException(400, f"Invalid action_id: {action_id}")

    # Validate allergen IDs
    for allergen_id in recipe_data["metadata"]["allergens"]:
        result = await db.execute(select(Allergen).where(Allergen.id == allergen_id))
        if not result.scalars().first():
            raise HTTPException(400, f"Invalid allergen_id: {allergen_id}")

    # Similarly validate claims, tools, etc.