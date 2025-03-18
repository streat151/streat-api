from sqlmodel import SQLModel, Field
from typing import Optional

class AllergenBase(SQLModel):
    id: str = Field(regex=r"^I[0-9A-F]{3}$", primary_key=True)
    abbreviation: str = Field(regex=r"^[A-Z]{3}$")
    name: str = Field(index=True)

class Allergen(AllergenBase, table=True):
    pass
