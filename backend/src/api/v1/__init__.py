from fastapi import APIRouter

from backend.src.api.v1 import auth, games, stream, websocket

# Этот роутер агрегирует все роутеры для v1
router = APIRouter()

router.include_router(auth.router)
router.include_router(games.router)
router.include_router(stream.router)
router.include_router(websocket.router)
