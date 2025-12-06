"""
FastAPI application entry point for Mentor platform.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mentor.api.middleware import LoggingMiddleware, RequestIdMiddleware
from mentor.api.routes import (
    analytics,
    assessment,
    auth,
    courses,
    materials,
    students,
    tutor,
    voice,
)
from mentor.config import settings
from mentor.db.session import close_db, init_db

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown."""
    # Startup
    logger.info("Starting Mentor API", env=settings.app_env)
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down Mentor API")
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Open-source platform for faculty-controlled AI tutoring and assessment",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)

    # Include API routes
    api_prefix = settings.api_v1_prefix
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(courses.router, prefix=api_prefix)
    app.include_router(materials.router, prefix=api_prefix)
    app.include_router(tutor.router, prefix=api_prefix)
    app.include_router(students.router, prefix=api_prefix)
    app.include_router(assessment.router, prefix=api_prefix)
    app.include_router(analytics.router, prefix=api_prefix)
    app.include_router(voice.router, prefix=api_prefix)

    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}

    return app


app = create_app()


def run() -> None:
    """Run the application using uvicorn."""
    import uvicorn

    uvicorn.run(
        "mentor.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
    )


if __name__ == "__main__":
    run()
