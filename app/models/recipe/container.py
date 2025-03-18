from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

class ContainerChildBase(SQLModel):
    id: str = Field(regex=r"^P[0-9A-F]{3}$", primary_key=True)
    name: str

class ContainerChild(ContainerChildBase, table=True):
    pass

class ContainerBase(SQLModel):
    name: str
    children: List[ContainerChild] = Field(default=[], sa_type="JSON")

class Container(ContainerBase, table=True):
    id: str = Field(default=None, primary_key=True)
