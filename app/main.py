import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from app.api.errors import register_error_handlers
from app.api.routes import router
from app.api.schemas import ApiResponse
from app.infrastructure.database import build_engine
from app.infrastructure.models import Base


def create_app(database_url: str | None = None):
    engine = build_engine(database_url or os.getenv("DATABASE_URL", "sqlite:///./studymanager.db"))

    @asynccontextmanager
    async def lifespan(app):
        Base.metadata.create_all(engine)
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="StudyManager API", version="1.0.0", lifespan=lifespan)
    app.state.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    register_error_handlers(app)
    app.include_router(router, responses={
        code: {"model": ApiResponse[None], "description": description}
        for code, description in {
            404: "Resource not found", 409: "Conflicting data",
            422: "Invalid request", 500: "Internal server error",
        }.items()
    })
    return app


app = create_app()
