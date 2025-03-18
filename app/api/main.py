from fastapi import APIRouter

from app.api.routes import login, users, recipe


# API router instance
api_router = APIRouter()

# Register API routers
api_router.include_router(login.router, tags=['auth'])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(recipe.router, prefix="/recipes", tags=["recipes"])
