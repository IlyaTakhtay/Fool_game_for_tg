from fastapi import Request
from fastapi.responses import JSONResponse

async def error_handling_middleware(request: Request, call_next):
    try:
        # Выполняем запрос
        response = await call_next(request)
        return response
    except Exception as exc:
        # Логируем ошибку (можно подключить логгер)
        print(f"Ошибка: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Произошла внутренняя ошибка сервера."},
        )
