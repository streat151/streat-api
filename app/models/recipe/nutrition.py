from sqlmodel import SQLModel, Field

class NutritionBase(SQLModel):
    id: str = Field(regex=r"^H[0-9A-F]{3}$", primary_key=True)
    abbreviation: str = Field(regex=r"^[A-Z]{3}$")
    name: str
    unit_id: str = Field(regex=r"^B[0-9A-F]{3}$")

class Nutrition(NutritionBase, table=True):
    pass
