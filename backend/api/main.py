from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from backend.api.middlewares import setup_middlewares
from backend.api.routers.games import router as games_router
from backend.api.routers.auth import router as auth_router
from backend.app.utils.logger import setup_logger

setup_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Приложение запущено!")
    yield
    print("Приложение остановлено!")


app = FastAPI(
    title="Fool Game API",
    version="1.0",
    lifespan=lifespan,
    # debug=True
)

setup_middlewares(app)

app.include_router(games_router)
app.include_router(auth_router)

if __name__ == "__main__":
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
