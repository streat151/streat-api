from sqlmodel import SQLModel, Field

class RestingTimeBase(SQLModel):
    id: str = Field(regex=r"^R[0-9A-F]{3}$", primary_key=True)
    name: str
    comment: str

class RestingTime(RestingTimeBase, table=True):
    pass
