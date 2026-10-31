from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import Engine

from app.auth.routes import router as auth_router
from app.config import Settings
from app.database import build_engine, database_available, get_engine
from app.projects.routes import router as projects_router


class LiveStatus(BaseModel):
    status: str = "ok"


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings if settings is not None else Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.engine = build_engine(config)
        try:
            yield
        finally:
            if application.state.engine is not None:
                application.state.engine.dispose()

    application = FastAPI(title="CHÁNH HƯNG PMIS", lifespan=lifespan)
    application.state.settings = config
    application.include_router(auth_router)
    application.include_router(projects_router)

    @application.get("/health/live", response_model=LiveStatus)
    def live() -> LiveStatus:
        return LiveStatus()

    @application.get("/health/ready", responses={503: {"description": "Database unavailable"}})
    def ready(engine: Engine | None = Depends(get_engine)) -> JSONResponse:
        if database_available(engine):
            return JSONResponse({"status": "ready", "database": "available"})
        return JSONResponse({"status": "not_ready", "database": "unavailable"}, status_code=503)

    return application


app = create_app()
