from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List, Optional

from sqlmodel import select

from app.models.user import Message
from app.crud import crud_nutrition as crud
from app.api.deps import SessionDep, CurrentUser
from app.models.nutrition.food_item import *
from app.models.nutrition.nutrition_entry import *
from app.models.nutrition.nutrition_average import *
from app.models.nutrition.outlier_flag import *
from app.models.nutrition.system_version import *


router = APIRouter()

@router.post("/foods/", response_model=FoodItemPublic, status_code=status.HTTP_201_CREATED)
async def create_food(
    food_in: FoodItemCreate,
    session: SessionDep,
    current_user: CurrentUser,  # Add auth if needed
) -> FoodItem:
    """
    Create a new food item.
    """
    return await crud.create_food_item(session=session, food_in=food_in)


@router.get("/foods/", response_model=FoodItemsPublic)
async def read_foods(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
) -> FoodItemsPublic:
    """
    Retrieve all food items.
    """
    return await crud.get_food_items(session=session, skip=skip, limit=limit)


@router.get("/foods/{food_id}", response_model=FoodItemPublic)
async def read_food(
    food_id: str,
    session: SessionDep,
) -> FoodItem:
    """
    Get a specific food item by ID.
    """
    food = await crud.get_food_item(session=session, food_id=food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food item not found")
    return food


@router.patch("/foods/{food_id}", response_model=FoodItemPublic)
async def update_food(
    food_id: str,
    food_in: FoodItemUpdate,
    session: SessionDep,
) -> FoodItem:
    """
    Update a food item.
    """
    return await crud.update_food_item(session=session, food_id=food_id, food_in=food_in)


@router.delete("/foods/{food_id}", response_model=Message)
async def delete_food(
    food_id: str,
    session: SessionDep,
) -> Message:
    """
    Delete a food item.
    """
    return await crud.delete_food_item(session=session, food_id=food_id)


@router.get("/foods/{food_id}/nutrition", response_model=dict)
async def get_food_nutrition(
    *,
    food_id: str,
    version: Optional[str] = None,  # e.g., "1.0.3.1"
    session: SessionDep,
) -> dict:
    """
    Get nutrition averages for a food item (latest or by version).
    """
    # If version is provided, fetch specific version; else fetch latest
    if version:
        averages = await session.exec(
            select(NutritionAverage)
            .where(NutritionAverage.food_id == food_id)
            .where(NutritionAverage.version_id == version)
        )
    else:
        # Find the latest version
        latest_version = await session.exec(
            select(SystemVersion)
            .order_by(SystemVersion.year.desc(), SystemVersion.month.desc(), SystemVersion.sub_version.desc())
            .limit(1)
        )
        latest_version = latest_version.first()
        if not latest_version:
            raise HTTPException(status_code=404, detail="No system versions found")
        version = latest_version.version_id
        averages = await session.exec(
            select(NutritionAverage)
            .where(NutritionAverage.food_id == food_id)
            .where(NutritionAverage.version_id == version)
        )

    # Format response
    nutrition_data = {}
    for avg in averages:
        nutrition_data[avg.nutrition_id] = {
            "value": avg.value,
            "unit": "kJ"  # Replace with actual unit from NutritionMetadata
        }

    return nutrition_data


@router.post("/nutrition-entries/", response_model=NutritionEntryPublic, status_code=status.HTTP_201_CREATED)
async def create_nutrition_entry(
    entry_in: NutritionEntryCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> NutritionEntry:
    """
    Create a new nutrition entry.
    """
    return await crud.create_nutrition_entry(session=session, entry_in=entry_in, user=current_user)


@router.get("/nutrition-entries/{entry_id}", response_model=NutritionEntryPublic)
async def read_nutrition_entry(
    entry_id: UUID,
    session: SessionDep,
) -> NutritionEntry:
    """
    Get a nutrition entry by ID.
    """
    entry = await crud.get_nutrition_entry(session=session, entry_id=entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Nutrition entry not found")
    return entry


@router.get("/nutrition-entries/", response_model=NutritionEntriesPublic)
async def read_nutrition_entries(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
) -> NutritionEntriesPublic:
    """
    Retrieve multiple nutrition entries with pagination.
    """
    return await crud.get_nutrition_entries(session=session, skip=skip, limit=limit)


@router.patch("/nutrition-entries/{entry_id}", response_model=NutritionEntryPublic)
async def update_nutrition_entry(
    entry_id: UUID,
    entry_in: NutritionEntryCreate,
    session: SessionDep,
) -> NutritionEntry:
    """
    Update a nutrition entry.
    """
    return await crud.update_nutrition_entry(session=session, entry_id=entry_id, entry_in=entry_in)


@router.delete("/nutrition-entries/{entry_id}", response_model=Message)
async def delete_nutrition_entry(
    entry_id: UUID,
    session: SessionDep,
) -> Message:
    """
    Delete a nutrition entry.
    """
    return await crud.delete_nutrition_entry(session=session, entry_id=entry_id)


@router.post("/nutrition-averages/", response_model=NutritionAveragePublic, status_code=status.HTTP_201_CREATED)
async def create_nutrition_average(
    average_in: NutritionAverageCreate,
    session: SessionDep,
) -> NutritionAverage:
    """
    Create a new nutrition average.
    """
    return await crud.create_nutrition_average(session=session, average_in=average_in)


@router.get("/nutrition-averages/{version_id}/{food_id}/{nutrition_id}", response_model=NutritionAveragePublic)
async def read_nutrition_average(
    version_id: str,
    food_id: str,
    nutrition_id: str,
    session: SessionDep,
) -> NutritionAverage:
    """
    Get a nutrition average by composite key.
    """
    average = await crud.get_nutrition_average(session=session, version_id=version_id, food_id=food_id, nutrition_id=nutrition_id)
    if not average:
        raise HTTPException(status_code=404, detail="Nutrition average not found")
    return average


@router.get("/nutrition-averages/", response_model=List[NutritionAveragePublic])
async def read_nutrition_averages(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
) -> List[NutritionAverage]:
    """
    Retrieve multiple nutrition averages with pagination.
    """
    return await crud.get_nutrition_averages(session=session, skip=skip, limit=limit)


@router.post("/outlier-flags/", response_model=OutlierFlagPublic, status_code=status.HTTP_201_CREATED)
async def create_outlier_flag(
    flag_in: OutlierFlagCreate,
    session: SessionDep,
) -> OutlierFlag:
    """
    Create a new outlier flag.
    """
    return await crud.create_outlier_flag(session=session, flag_in=flag_in)


@router.get("/outlier-flags/{flag_id}", response_model=OutlierFlagPublic)
async def read_outlier_flag(
    flag_id: int,
    session: SessionDep,
) -> OutlierFlag:
    """
    Get an outlier flag by ID.
    """
    flag = await crud.get_outlier_flag(session=session, flag_id=flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Outlier flag not found")
    return flag


@router.get("/outlier-flags/", response_model=List[OutlierFlagPublic])
async def read_outlier_flags(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
) -> List[OutlierFlag]:
    """
    Retrieve multiple outlier flags with pagination.
    """
    return await crud.get_outlier_flags(session=session, skip=skip, limit=limit)


@router.post("/system-versions/", response_model=SystemVersionPublic, status_code=status.HTTP_201_CREATED)
async def create_system_version(
    version_in: SystemVersionCreate,
    session: SessionDep,
) -> SystemVersion:
    """
    Create a new system version.
    """
    return await crud.create_system_version(session=session, version_in=version_in)


@router.get("/system-versions/{version_id}", response_model=SystemVersionPublic)
async def read_system_version(
    version_id: str,
    session: SessionDep,
) -> SystemVersion:
    """
    Get a system version by ID.
    """
    version = await crud.get_system_version(session=session, version_id=version_id)
    if not version:
        raise HTTPException(status_code=404, detail="System version not found")
    return version


@router.get("/system-versions/", response_model=List[SystemVersionPublic])
async def read_system_versions(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
) -> List[SystemVersion]:
    """
    Retrieve multiple system versions with pagination.
    """
    return await crud.get_system_versions(session=session, skip=skip, limit=limit)
