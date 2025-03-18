from sqlmodel import SQLModel, Field

class ThicknessBase(SQLModel):
    id: str = Field(regex=r"^G[0-9A-F]{3}$", primary_key=True)
    name: str
    comment: str

class Thickness(ThicknessBase, table=True):
    pass
