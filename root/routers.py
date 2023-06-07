from fastapi import APIRouter

from standalone import views

api_router = APIRouter(prefix="/api")

api_router.include_router(views.router)
