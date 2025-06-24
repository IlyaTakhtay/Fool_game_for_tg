import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from backend.api.middlewares import setup_middlewares
from backend.api.routers.games import router as games_router
from backend.api.routers.auth import router as auth_router
from backend.api.routers.stream import router as stream_router
from backend.api.routers.websocket import router as websocket_router
from backend.app.config.logging_config import setup_logging
from backend.app.config.settings import DEBUG


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Приложение запущено!")
    setup_logging()
    yield
    logging.info("Приложение остановлено!")


app = FastAPI(
    title="Fool Game API",
    version="1.0",
    lifespan=lifespan,
    # debug=True
)

setup_middlewares(app)

app.include_router(games_router)
app.include_router(auth_router)
app.include_router(stream_router)
app.include_router(websocket_router)

if __name__ == "__main__":
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
