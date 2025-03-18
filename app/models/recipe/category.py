from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

class SubcategoryBase(SQLModel):
    id: str = Field(regex=r"^K[0-9A-F]{3}$", primary_key=True)
    name: str

class Subcategory(SubcategoryBase, table=True):
    pass

class CategoryBase(SQLModel):
    id: str = Field(regex=r"^K[0-9A-F]{3}$", primary_key=True)
    name: str
    subcategories: List[Subcategory] = Field(default=[], sa_type="JSON")

class Category(CategoryBase, table=True):
    pass
