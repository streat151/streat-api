from datetime import datetime
from typing import Optional
from sqlmodel import Field, Relationship
from sqlmodel import SQLModel
from .food_item import FoodItem


class NutritionAverageBase(SQLModel):
    version_id: str = Field(primary_key=True)
    food_id: str = Field(foreign_key="fooditem.id", primary_key=True)
    nutrition_id: str = Field(primary_key=True)
    value: float

class NutritionAverage(NutritionAverageBase, table=True):
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NutritionAverageCreate(NutritionAverageBase):
    pass

class NutritionAveragePublic(NutritionAverageBase):
    created_at: datetime
