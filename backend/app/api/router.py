from fastapi import APIRouter

from app.api.routes import demo_routing, hazards, health, missions, imagery, report

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(missions.router)
api_router.include_router(demo_routing.router)
api_router.include_router(hazards.router)
api_router.include_router(imagery.router)
api_router.include_router(report.router)
