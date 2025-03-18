import uuid
from typing import List
from datetime import datetime

from pydantic import EmailStr
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel, Relationship

from app.models.recipe.recipe import UserRecipeSave


# Shared properties
class UserBase(SQLModel):
    username: str = Field(unique=True, index=True, max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = False


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    password_hash: str
    joined_date: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), 
            server_default=func.now()
        )
    )

    # Relationship for recipes the user has saved
    saved_recipes: List[UserRecipeSave] = Relationship(back_populates="user")

    # Following relationships
    following_relationships: List["UserFollow"] = Relationship(back_populates="follower")
    follower_relationships: List["UserFollow"] = Relationship(back_populates="followed")
    
    # Convenience properties to get actual User instances
    @property
    def following(self) -> List["User"]:
        return [rel.followed for rel in self.following_relationships]
    
    @property
    def followers(self) -> List["User"]:
        return [rel.follower for rel in self.follower_relationships]
    
    # Recipe lists relationship
    recipe_lists: List["RecipeList"] = Relationship(back_populates="user") # type: ignore


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    username: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=40)
    is_active: bool = Field(default=True)


class UserUpdateMe(SQLModel):
    username: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int

class UserFollow(SQLModel, table=True):
    follower_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    followed_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    # Relationships
    follower: "User" = Relationship(back_populates="following_relationships")
    followed: "User" = Relationship(back_populates="follower_relationships")


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


# Generic message
class Message(SQLModel):
    message: str
