import uuid

from datetime import datetime
from typing import Optional, List
from sqlmodel import Field
from sqlmodel import SQLModel


class NutritionEntryBase(SQLModel):
    food_id: str = Field(foreign_key="fooditem.id")
    nutrition_id: str  # e.g., "H001"
    value: float
    source: str  # e.g., "manual", "csv_import", "api"
    created_by: uuid.UUID = Field(foreign_key="user.id")

class NutritionEntry(NutritionEntryBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4(), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NutritionEntryCreate(NutritionEntryBase):
    pass

class NutritionEntryPublic(NutritionEntryBase):
    id: uuid.UUID
    created_at: datetime

class NutritionEntriesPublic(SQLModel):
    data: List[NutritionEntryPublic]
    count: int
