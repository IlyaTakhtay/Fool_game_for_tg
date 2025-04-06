from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from backend.api.routers.games import router as games_router
from backend.app.utils.logger import setup_logger

setup_logger("main")

# Асинхронный контекстный менеджер для обработки событий
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код выполнится при запуске приложения
    print("Приложение запущено!")
    yield
    # Код выполнится при остановке приложения
    print("Приложение остановлено!")

# Создаем приложение с lifespan-обработчиком
app = FastAPI(
    title="Fool Game API", 
    version="1.0",
    lifespan=lifespan,  # Подключаем обработчик жизненного цикла #TODO: это че такое?
    debug=True
)

# Подключаем маршруты
app.include_router(games_router)

if __name__ == '__main__':
    uvicorn.run("backend.api.main:app", host='0.0.0.0', port=8000, reload=True)
