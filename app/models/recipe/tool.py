from sqlmodel import SQLModel, Field

class ToolBase(SQLModel):
    id: str = Field(regex=r"^E[0-9A-F]{3}$", primary_key=True)
    name: str
    comment: str

class Tool(ToolBase, table=True):
    pass
