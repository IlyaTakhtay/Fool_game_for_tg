import logging
import uvicorn
from contextlib import asynccontextmanager
from dishka import Container
from fastapi import FastAPI

from dishka.integrations.fastapi import setup_dishka
from backend.src.api.middlewares import setup_middlewares
from backend.src.settings import AppSettings, CorsSettings
from backend.src.di import create_container
from backend.src.logging_config import setup_logging
from backend.src.api.responses import MsgSpecJSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logging.info("Приложение запущено!")
    yield
    container: Container = app.state.dishka_container
    await container.close()
    logging.info("Приложение остановлено!")


def create_app() -> FastAPI:
    """Фабрика приложения"""
    app = FastAPI(
        title="Fool Game API",
        version="1.0",
        lifespan=lifespan,
        default_response_class=MsgSpecJSONResponse,
    )

    # Setup DI
    container = create_container()
    setup_dishka(container=container, app=app)

    # Setup middlewares
    cors_settings = CorsSettings()
    setup_middlewares(app, cors_settings)

    # Register routers
    from backend.src.api.v1 import router as v1_router
    app.include_router(v1_router, prefix="/api/v1")

    return app


app = create_app()

if __name__ == "__main__":
    app_settings = AppSettings()
    uvicorn.run(
        "backend.src.main:app",
        host=app_settings.host,
        port=app_settings.port,
        reload=app_settings.reload,
    )
