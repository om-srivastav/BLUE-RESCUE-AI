from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.models import Hazard, Mission, MissionAOI, RouteCalculation  # noqa: F401 - register tables
from app.services.seed import seed_demo
from app.services.providers import ProviderNotConfigured


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo(db)
    yield


app = FastAPI(title="BLUE-RESCUE AI", version="0.1.0", lifespan=lifespan)


@app.exception_handler(ProviderNotConfigured)
async def provider_not_configured(_, error: ProviderNotConfigured):
    return JSONResponse(status_code=503, content={"detail": {"code": error.code, "message": str(error), "provider": error.family}})


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
