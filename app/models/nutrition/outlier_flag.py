import uuid

from datetime import datetime
from typing import Optional
from sqlmodel import Field
from sqlmodel import SQLModel


class OutlierFlagBase(SQLModel):
    entry_id: str = Field(foreign_key="nutritionentry.id")
    flagged_by: Optional[uuid.UUID] = Field(foreign_key="user.id")  # NULL if auto-detected
    decision: str  # "pending", "keep", "delete"
    reviewed_by: Optional[uuid.UUID] = Field(foreign_key="user.id")
    reviewed_at: Optional[datetime] = None

class OutlierFlag(OutlierFlagBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4(), primary_key=True)

class OutlierFlagCreate(OutlierFlagBase):
    pass

class OutlierFlagPublic(OutlierFlagBase):
    id: uuid.UUID
    created_at: datetime
