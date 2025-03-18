from datetime import datetime
from typing import Optional
from sqlmodel import Field
from sqlmodel import SQLModel


class SystemVersionBase(SQLModel):
    version_id: str = Field(primary_key=True)
    year: int
    month: int
    sub_version: int
    description: Optional[str] = None

class SystemVersion(SystemVersionBase, table=True):
    published_at: datetime = Field(default_factory=datetime.utcnow)

class SystemVersionCreate(SystemVersionBase):
    pass

class SystemVersionPublic(SystemVersionBase):
    published_at: datetime
