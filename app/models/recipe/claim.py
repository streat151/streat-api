import enum
from sqlmodel import SQLModel, Field
from typing import Optional

class ClaimType(str, enum.Enum):
    nutrient_related = "nutrient_related"
    dietary_form = "dietary_form"

class ClaimBase(SQLModel):
    id: str = Field(regex=r"^J[0-9A-F]{3}$", primary_key=True)
    abbreviation: str = Field(regex=r"^[A-Z]{4}$")
    name: str = Field(index=True)
    category: ClaimType

class Claim(ClaimBase, table=True):
    pass
