import logging
from jsonschema.exceptions import ValidationError

from sqlmodel import select, SQLModel
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.crud import crud_user

from app.core.config import settings
from app.utils.data_loader import load_data

from app.models.user import User, UserCreate
from app.models.recipe.recipe import Recipe
from app.models.recipe.tool import Tool
from app.models.recipe.unit import Unit
from app.models.recipe.claim import Claim
from app.models.recipe.action import Action
from app.models.recipe.allergen import Allergen
from app.models.recipe.critical_control_point import CriticalControlPoint
from app.models.recipe.nutrition import Nutrition
from app.models.recipe.resting_time import RestingTime
from app.models.recipe.category import Category
from app.models.recipe.thickness import Thickness
from app.models.recipe.container import Container


# Use an async engine
DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)
engine = create_async_engine(DATABASE_URL, pool_size=10)

# AsyncSession maker
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db() -> None:
    """NOTE: Tables should be created with Alembic migrations"""

    # Create tables (if not already created)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # Create superusers
    superusers = settings.SUPERUSERS
    async with AsyncSessionLocal() as session:
        for superuser in superusers:
            results = await session.execute(
                select(User).where(User.email == superuser)
            )
            user = results.scalars().first()
            if not user:
                user_in = UserCreate(
                    email=superuser,
                    password=settings.SUPERUSER_PASSWORD,
                    is_superuser=True,
                )
                await crud_user.create_user(session=session, user_create=user_in)
        
        # Prepopulate REFERENCE tables (actions, allergens, etc.)
        tables_to_prepopulate = [
            (Action, "actions.json", "actions.schema.json", "actions"),
            (Allergen, "allergens.json", "allergens.schema.json", "allergens"),
            (Claim, "claims.json", "claims.schema.json", "claims"),
            (Tool, "tools.json", "tools.schema.json", "tools"),
            (Unit, "units.json", "units.schema.json", "units"),
            (CriticalControlPoint, "critical_control_points.json", "critical_control_points.schema.json", "critical_control_points"),
            (Nutrition, "nutritions.json", "nutritions.schema.json", "nutritions"),
            (RestingTime, "resting_times.json", "resting_times.schema.json", "resting_times"),
            (Thickness, "thickness.json", "thickness.schema.json", "thickness_terms"),
            (Category, "categories.json", "categories.schema.json", "categories"),
            (Container, "container.json", "container.schema.json", "container"),
        ]

        for model, data_file, schema_file, key in tables_to_prepopulate:
            result = await session.execute(select(model))
            record = result.scalars().all()
            if not record:
                try:
                    await load_data(
                        session=session,
                        model=model,
                        data_file=f"app/data/{data_file}",
                        schema_file=f"app/schemas/{schema_file}",
                        key=key
                    )
                except ValidationError as e:
                    logging.info(str(e))
                    continue

        # Prepopulate RECIPE table (only if you have sample recipes)
        # if not await session.execute(select(Recipe)).scalars().first():
        #     await load_data(
        #         session=session,
        #         model=Recipe,
        #         data_file="app/data/recipe.json",
        #         schema_file="app/schemas/recipe.schema.json",
        #         key="recipes"
        #     )
