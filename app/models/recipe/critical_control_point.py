from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

class CriticalControlPointBase(SQLModel):
    id: str = Field(regex=r"^M[0-9A-F]{3}$", primary_key=True)
    name: str
    description: str
    unit_type: Optional[str] = None
    allowed_units: List[str] = Field(default=[], sa_type="JSON")
    format: Optional[str] = None
    allowed_values: List[str] = Field(default=[], sa_type="JSON")
    parameters: List[dict] = Field(default=[], sa_type="JSON")
    monitoring_guidelines: Optional[dict] = Field(default=None, sa_type="JSON")

class CriticalControlPoint(CriticalControlPointBase, table=True):
    pass
