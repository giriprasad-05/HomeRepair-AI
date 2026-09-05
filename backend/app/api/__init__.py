from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.appliances import router as appliances_router
from app.api.issues import router as issues_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(appliances_router)
api_router.include_router(issues_router)

__all__ = ["api_router"]
