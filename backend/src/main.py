import logging
from contextlib import asynccontextmanager
from dishka import Container
from fastapi import FastAPI
import uvicorn
from dishka.integrations.fastapi import setup_dishka

from backend.src.api.middlewares import setup_middlewares
from backend.src.settings import AppSettings, CorsSettings
from backend.src.di.providers import create_container
from backend.src.logging_config import setup_logging


def register_routers(app: FastAPI) -> None:
    """Регистрация роутеров"""
    from backend.src.api.routers.games import router as games_router
    from backend.src.api.routers.auth import router as auth_router
    from backend.src.api.routers.stream import router as stream_router
    from backend.src.api.routers.websocket import router as websocket_router

    app.include_router(games_router)
    app.include_router(auth_router)
    app.include_router(stream_router)
    app.include_router(websocket_router)


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
    )

    # Setup DI
    container = create_container()
    setup_dishka(container=container, app=app)

    # Setup middlewares
    cors_settings = CorsSettings()
    setup_middlewares(app, cors_settings)

    # Register routers
    register_routers(app)

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
