import enum
from sqlmodel import SQLModel, Field
from typing import Optional

class UnitType(str, enum.Enum):
    weight = "weight"
    volume = "volume"
    length = "length"
    time = "time"
    temperature = "temperature"
    count = "count"
    energy = "energy"

class UnitBase(SQLModel):
    id: str = Field(regex=r"^B[0-9A-F]{3}$", primary_key=True)
    name: str
    type: UnitType
    conversion_factor: Optional[float]
    conversion_formula: Optional[str]

class Unit(UnitBase, table=True):
    pass
