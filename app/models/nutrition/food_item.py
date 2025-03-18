import uuid
from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, Relationship
from sqlmodel import SQLModel


class FoodItemBase(SQLModel):
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None

class FoodItem(FoodItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4(), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    nutrition_entries: List["NutritionEntry"] = Relationship(back_populates="food_item") # type: ignore
    nutrition_averages: List["NutritionAverage"] = Relationship(back_populates="food_item") # type: ignore

class FoodItemCreate(FoodItemBase):
    pass

class FoodItemPublic(FoodItemBase):
    id: uuid.UUID
    name: str
    created_at: datetime

class FoodItemsPublic(SQLModel):
    data: List[FoodItemPublic]
    count: int

class FoodItemUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
