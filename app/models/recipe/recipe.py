from pydantic import model_validator
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, DateTime, func, JSON
from typing import List, Optional, Literal, Union
import uuid
from datetime import datetime

# ---------------------------
# Core Schema Models
# ---------------------------

class TimedQuantity(SQLModel):
    value: float = Field(ge=0)
    unit_id: str = Field(regex=r"^B[0-9A-F]{3}$")

class ComponentReference(SQLModel):
    internal_id: str = Field(regex=r"^C[0-9A-F]{3}$")
    quantity: TimedQuantity

class FormatVersion(SQLModel):
    major: int = Field(ge=1)
    minor: int = Field(ge=0)
    compatibility_hash: Optional[str] = Field(regex=r"^[A-F0-9]{4}-[A-F0-9]{4}$")
    model_config = {"arbitrary_types_allowed": True}

class RestingTime(SQLModel):
    value: float
    unit_id: str = Field(regex=r"^B[0-9A-F]{3}$")
    resting_definition_id: str = Field(regex=r"^R[0-9A-F]{3}$")

class Metadata(SQLModel):
    recipe_code: str = Field(regex=r"^[1-9A-F]{7}-[1-9A-F]{5}$")
    base_idea_from: Optional[str] = ""
    resting_times: List[RestingTime] = []
    
    class Config:
        extra = "allow"

class RawMaterialIngredient(SQLModel):
    type: Literal["raw_material"]
    ingredient_id: str = Field(regex=r"^[A-F0-9]{7}$")
    internal_id: str = Field(regex=r"^C[0-9A-F]{3}$")
    quantity: TimedQuantity

class SubRecipeIngredient(SQLModel):
    type: Literal["sub_recipe"]
    # recipe_code: str = Field(regex=r"^[1-9A-F]{7}-[1-9A-F]{5}$")
    internal_id: str = Field(regex=r"^C[0-9A-F]{3}$")
    quantity: TimedQuantity

Ingredient = Union[RawMaterialIngredient, SubRecipeIngredient]

class Step(SQLModel):
    step_id: str = Field(regex=r"^S[0-9A-F]{3}$")
    components: List[ComponentReference] = []
    ccp_checkpoints: List[str] = Field(regex=r"^M[0-9A-F]{3}$", default=[])

class Instructions(SQLModel):
    steps: List[Step]

class NutritionValue(SQLModel):
    nutrition_id: str = Field(regex=r"^H[0-9A-F]{3}$")
    per_serving: Optional[float] = None
    per_100g: Optional[float] = None
    per_100ml: Optional[float] = None
    unit_id: str = Field(regex=r"^B[0-9A-F]{3}$")

    @model_validator(mode="after")
    def require_one_nutrition_value(cls, v, info):
        if v.per_serving is not None or v.per_100g is not None or v.per_100ml is not None:
            return v
        raise ValueError("At least one nutrition value must be provided")

    # @model_validator(mode="after")
    # def require_one_nutrition_value(cls, v, values):
    #     if 'per_serving' in values or 'per_100g' in values or 'per_100ml' in values:
    #         return v
    #     raise ValueError("At least one nutrition value must be provided")

class Nutrition(SQLModel):
    values: List[NutritionValue]
    base_units: List[Literal["per_serving", "per_100g", "per_100ml"]] = []

class Container(SQLModel):
    id: str = Field(regex=r"^P[0-9A-F]{3}$")

class ServingInfo(SQLModel):
    count: int = Field(ge=1)
    container: Optional[Container]

class DigitalSignature(SQLModel):
    algorithm: Literal["ED25519", "ECDSA", "RSA"]
    public_key: Optional[str]
    signature: str

class Validation(SQLModel):
    digital_signature: DigitalSignature

class Image(SQLModel):
    urn: str = Field(regex=r"^urn:recipeimg:sha3-[a-f0-9]{64}$")
    license: Optional[str]

class VisualReferences(SQLModel):
    system: str = Field(regex=r"^urn:recipeimg:v[1-9]$")
    images: List[Image] = []

# ---------------------------
# Association Model
# ---------------------------

class UserRecipeSave(SQLModel, table=True):
    user_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    recipe_id: uuid.UUID = Field(foreign_key="recipe.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Back-reference relationships
    user: "User" = Relationship(back_populates="saved_recipes") # type: ignore
    # recipe: "Recipe" = Relationship(back_populates="saved_by")
    recipe: "Recipe" = Relationship(back_populates="saved_by", sa_relationship_kwargs={"cascade": "delete"})

# ---------------------------
# Database Model
# ---------------------------
class RecipeListRecipe(SQLModel, table=True):
    recipe_list_id: uuid.UUID = Field(foreign_key="recipelist.id", primary_key=True)
    recipe_id: uuid.UUID = Field(foreign_key="recipe.id", primary_key=True)
    added_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

class RecipeBase(SQLModel):
    title: str
    # All recipes are public by default (not private)
    private: bool = Field(default=False)
    # Set in API route as current user's ID
    author_id: uuid.UUID
    format_version: FormatVersion = Field(sa_type=JSON)
    recipe_metadata: Metadata = Field(sa_type=JSON)
    ingredients: List[Ingredient] = Field(sa_type=JSON)
    instructions: Instructions = Field(sa_type=JSON)
    nutrition: Nutrition = Field(sa_type=JSON)
    serving_info: ServingInfo = Field(sa_type=JSON)
    validation: Validation | None = Field(default=None, sa_type=JSON)
    visual_references: VisualReferences | None = Field(default=None, sa_type=JSON)

class Recipe(RecipeBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    description: str
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), 
            server_default=func.now()
        )
    )
    last_modified_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now()
        )
    )
    save_count: int = Field(default=0)
    version_number: int = Field(default=1, ge=1)
    original_recipe_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="recipe.id",
        description="Root version of this recipe"
    )
    previous_version_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="recipe.id",
        description="Immediately preceding version"
    )
    # Relationship for users who saved this recipe
    saved_by: List[UserRecipeSave] = Relationship(back_populates="recipe")
    recipe_lists: List["RecipeList"] = Relationship(back_populates="recipes", link_model=RecipeListRecipe)

# ---------------------------
# Pydantic Models for API
# ---------------------------

class RecipeCreate(RecipeBase):
    pass

class RecipeUpdate(SQLModel):
    title: Optional[str] = None
    author_id: Optional[uuid.UUID] = None
    format_version: Optional[FormatVersion] = None
    recipe_metadata: Optional[Metadata] = None
    ingredients: Optional[List[Union[RawMaterialIngredient, SubRecipeIngredient]]] = None
    instructions: Optional[Instructions] = None
    nutrition: Optional[Nutrition] = None
    serving_info: Optional[ServingInfo] = None
    validation: Optional[Validation] = None
    visual_references: Optional[VisualReferences] = None

class RecipePublic(RecipeBase):
    id: uuid.UUID
    created_at: datetime
    last_modified_at: datetime
    save_count: int
    version_number: int
    original_recipe_id: Optional[uuid.UUID] = None
    previous_version_id: Optional[uuid.UUID] = None
    current_author_id: uuid.UUID = Field(
        description="User who created THIS version",
        foreign_key="user.id"
    )

class RecipesPublic(SQLModel):
    data: list[RecipePublic]
    count: int

class RecipeList(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True)
    private: bool = Field(default=False)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    last_modified_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    # Relationships
    user: "User" = Relationship(back_populates="recipe_lists") # type: ignore
    recipes: List["Recipe"] = Relationship(back_populates="recipe_lists", link_model=RecipeListRecipe)
