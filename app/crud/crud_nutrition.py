from sqlmodel import select, func
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID

from app.models.nutrition.food_item import *
from app.models.nutrition.nutrition_entry import *
from app.models.nutrition.nutrition_average import *
from app.models.nutrition.outlier_flag import *
from app.models.nutrition.system_version import *
from app.models.user import User, Message
from app.api.deps import SessionDep


async def create_food_item(session: SessionDep, food_in: FoodItemCreate) -> FoodItem:
    """
    Create a new food item.
    """
    # Check for existing food item with the same name
    existing_food = await session.exec(
        select(FoodItem).where(FoodItem.name == food_in.name)
    )
    if existing_food.first():
        raise HTTPException(
            status_code=400,
            detail="A food item with this name already exists.",
        )
    food = FoodItem(**food_in.dict())
    session.add(food)
    await session.commit()
    await session.refresh(food)
    return food

async def get_food_item(session: SessionDep, food_id: str) -> Optional[FoodItem]:
    """
    Get a food item by ID.
    """
    return await session.get(FoodItem, food_id)

async def get_food_items(session: SessionDep, skip: int = 0, limit: int = 100) -> FoodItemsPublic:
    """
    Retrieve multiple food items with pagination.
    """
    count_statement = select(func.count()).select_from(FoodItem)
    count = (await session.execute(count_statement)).scalar()

    statement = select(FoodItem).offset(skip).limit(limit)
    results = await session.execute(statement)
    food_items = results.scalars().all()

    return FoodItemsPublic(data=food_items, count=count)

async def update_food_item(
    session: SessionDep, food_id: str, food_in: FoodItemUpdate
) -> FoodItem:
    """
    Update a food item.
    """
    food = await session.get(FoodItem, food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food item not found")

    # Check for name uniqueness if updating name
    if food_in.name:
        existing_food = await session.exec(
            select(FoodItem).where(FoodItem.name == food_in.name)
        )
        if existing_food.first() and existing_food.first().id != food_id:
            raise HTTPException(
                status_code=400,
                detail="A food item with this name already exists.",
            )

    # Update fields
    for key, value in food_in.dict(exclude_unset=True).items():
        setattr(food, key, value)

    session.add(food)
    await session.commit()
    await session.refresh(food)
    return food

async def delete_food_item(session: SessionDep, food_id: str) -> Message:
    """
    Delete a food item.
    """
    food = await session.get(FoodItem, food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food item not found")

    await session.delete(food)
    await session.commit()
    return Message(message="Food item deleted successfully")

async def create_nutrition_entry(session: SessionDep, entry_in: NutritionEntryCreate, user: User) -> NutritionEntry:
    """
    Create a new nutrition entry.
    """
    entry = NutritionEntry(**entry_in.dict(), created_by=user.id)
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry

async def get_nutrition_entry(session: SessionDep, entry_id: UUID) -> Optional[NutritionEntry]:
    """
    Get a nutrition entry by ID.
    """
    return await session.get(NutritionEntry, entry_id)

async def get_nutrition_entries(session: SessionDep, skip: int = 0, limit: int = 100) -> NutritionEntriesPublic:
    """
    Retrieve multiple nutrition entries with pagination.
    """
    count_statement = select(func.count()).select_from(NutritionEntry)
    count_result = await session.execute(count_statement)
    count = count_result.scalar()

    statement = select(NutritionEntry).offset(skip).limit(limit)
    results = await session.execute(statement)
    entries = results.scalars().all()

    return NutritionEntriesPublic(data=entries, count=count)

async def update_nutrition_entry(session: SessionDep, entry_id: UUID, entry_in: NutritionEntryCreate) -> NutritionEntry:
    """
    Update a nutrition entry.
    """
    entry = await session.get(NutritionEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Nutrition entry not found")

    for key, value in entry_in.dict().items():
        setattr(entry, key, value)

    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry

async def delete_nutrition_entry(session: SessionDep, entry_id: UUID) -> Message:
    """
    Delete a nutrition entry.
    """
    entry = await session.get(NutritionEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Nutrition entry not found")

    await session.delete(entry)
    await session.commit()
    return Message(message="Nutrition entry deleted successfully")

async def create_nutrition_average(session: SessionDep, average_in: NutritionAverageCreate) -> NutritionAverage:
    """
    Create a new nutrition average.
    """
    average = NutritionAverage(**average_in.dict())
    session.add(average)
    await session.commit()
    await session.refresh(average)
    return average

async def get_nutrition_average(session: SessionDep, version_id: str, food_id: str, nutrition_id: str) -> Optional[NutritionAverage]:
    """
    Get a nutrition average by composite key.
    """
    return await session.get(NutritionAverage, (version_id, food_id, nutrition_id))

async def get_nutrition_averages(session: SessionDep, skip: int = 0, limit: int = 100) -> List[NutritionAverage]:
    """
    Retrieve multiple nutrition averages with pagination.
    """
    statement = select(NutritionAverage).offset(skip).limit(limit)
    results = await session.execute(statement)
    return results.scalars().all()

async def create_outlier_flag(session: SessionDep, flag_in: OutlierFlagCreate) -> OutlierFlag:
    """
    Create a new outlier flag.
    """
    flag = OutlierFlag(**flag_in.dict())
    session.add(flag)
    await session.commit()
    await session.refresh(flag)
    return flag

async def get_outlier_flag(session: SessionDep, flag_id: int) -> Optional[OutlierFlag]:
    """
    Get an outlier flag by ID.
    """
    return await session.get(OutlierFlag, flag_id)

async def get_outlier_flags(session: SessionDep, skip: int = 0, limit: int = 100) -> List[OutlierFlag]:
    """
    Retrieve multiple outlier flags with pagination.
    """
    statement = select(OutlierFlag).offset(skip).limit(limit)
    results = await session.execute(statement)
    return results.scalars().all()

async def create_system_version(session: SessionDep, version_in: SystemVersionCreate) -> SystemVersion:
    """
    Create a new system version.
    """
    version = SystemVersion(**version_in.dict())
    session.add(version)
    await session.commit()
    await session.refresh(version)
    return version

async def get_system_version(session: SessionDep, version_id: str) -> Optional[SystemVersion]:
    """
    Get a system version by ID.
    """
    return await session.get(SystemVersion, version_id)

async def get_system_versions(session: SessionDep, skip: int = 0, limit: int = 100) -> List[SystemVersion]:
    """
    Retrieve multiple system versions with pagination.
    """
    statement = select(SystemVersion).offset(skip).limit(limit)
    results = await session.execute(statement)
    return results.scalars().all()
