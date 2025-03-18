from sqlmodel import SQLModel, Field, JSON
from typing import List, Optional

class ActionBase(SQLModel):
    id: str = Field(regex=r"^F[0-9A-F]{3}$", primary_key=True)
    name: str = Field(index=True)
    parameters: List[str] = Field(default=[], sa_type=JSON)

class Action(ActionBase, table=True):
    pass
