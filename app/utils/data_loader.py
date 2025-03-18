import json
from sqlmodel import select
from jsonschema import validate
from sqlalchemy.ext.asyncio import AsyncSession


async def load_data(
    session: AsyncSession,
    model,  # SQLModel class (e.g., Action, Allergen)
    data_file: str,
    schema_file: str,
    key: str  # Key in JSON (e.g., "actions", "allergens")
):
    # Load JSON data
    with open(data_file, "r") as f:
        data = json.load(f)[key]
    
    # Validate against schema
    with open(schema_file, "r") as f:
        schema = json.load(f)
        validate(instance={key: data}, schema=schema)
    
    # Insert into database
    for item in data:
        # Check if the item already exists
        result = await session.execute(select(model).where(model.id == item["id"]))
        if not result.scalars().first():
            db_item = model(**item)
            session.add(db_item)
    await session.commit()
