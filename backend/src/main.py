from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging import logger
from api.router import api_router
from knowledge.snapshot import snapshot_manager
from memory.store import memory_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} [{settings.app_env}]...")
    try:
        snapshot_manager.refresh()
    except Exception as e:
        logger.warning(f"Initial knowledge snapshot load deferred or partial: {e}")

    try:
        await memory_store.initialize()
    except Exception as e:
        logger.warning(f"Database memory initialization deferred: {e}")

    yield

    logger.info(f"Shutting down {settings.app_name}...")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="FastAPI Backend for LCK Airport AI Talking Avatar",
        version="0.1.0",
        lifespan=lifespan
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()

