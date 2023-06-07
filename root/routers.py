from fastapi import APIRouter

from standalone import views

router = APIRouter(prefix="/api")

router.include_router(views.router)
