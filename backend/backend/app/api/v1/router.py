from fastapi import APIRouter

from app.api.v1.routes import events, execution, health, preferences, scans

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(preferences.router)
api_router.include_router(scans.router)
api_router.include_router(execution.router)
api_router.include_router(events.router)
