import logging
import sys
import os
import uuid
import json
import msgspec
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    Query,
    WebSocket,
    WebSocketException,
    WebSocketDisconnect,
    status,
    Request,
    HTTPException
)
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse

# from fastapi.staticfiles import StaticFiles
import redis.asyncio as asyncredis
import asyncpg  # type: ignore
import msgspec


import backend.app.game_interface as Game

logging.basicConfig(
    level=logging.DEBUG,  # Уровень логирования(DEBUG,INFO,WARNING,ERROR,CRIT)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

redis = asyncredis.Redis(
    host='redis_cache',
    password='123',
    port=6379
)

postgres = asyncpg.connect(
    database='postgres',
    user='postgres',
    host='postgres_db',
    password='postgres',
    port=5432
)



# pre-start and pre-stop functionality
@asynccontextmanager
async def db_lifespan(app: FastAPI):
    redis
    logging.debug(await redis.ping())
    logging.debug('mohca')
    # await postgres.ping()
    yield
    logging.debug(await redis.ping())
    logging.debug(await postgres.connection.close())

app = FastAPI(docs_url="/docs", lifespan=db_lifespan)

# "https://example.com", "http://localhost:3000"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешённые домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: придумать как в доке сделать инфу по апи сокета

app.mount("/static", StaticFiles(directory="app/templates"), name="static")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except RuntimeError as e:
            # Логируем ошибку, если сообщение не удалось отправить
            logging.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(
            self,
            message,
            except_sender: WebSocket | None = None
            ):
        for connection in self.active_connections:
            if connection != except_sender:  # Исключаем отправителя
                try:
                    await connection.send_text(message)
                except RuntimeError as e:
                    # Логируем ошибку, если сообщение не удалось отправить
                    logging.error(f"Failed to broadcast message to a connection: {e}")
                    self.disconnect(connection)


manager = ConnectionManager()
games: list[Game.GameState] = [] # upgrade to set
game_connections: dict[int, list[WebSocket]] = {} # upgrade to dict format game_id: {player: Websocket | None} ??? why no usage


@app.get("/")
async def get():
    return FileResponse("app/templates/index_2.html")


@app.websocket("/ws/{game_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: int, player_id: str):
    """
    WebSocket Endpoint.

    ## Usage:
    - Connect to `/ws`.
    - Send and receive JSON-encoded messages.
    - Example message format:
    recive
    ```json
    {
        "action": "defend",
        "user_id": "sekg23dg",
        "defend_card": { "suit": "hearts", "rank": "queen" },
        "attack_card": { "suit": "spades", "rank": "king" }
    }
    ```
    ```json
    {
        "action": "attack",
        "user_id": "sasach69",
        "attack_card": { "suit": "spades", "rank": "king" }
    }
    {
        "action": "ready"/"drawback",
        "user_id": "mesus",
    }
    ```
    send
    ```json
    {
        "action": "update_status",
        "user_id": "sasach69",
    }
    {
        "action": "update_table",
        "attack_card": { "suit": "spades", "rank": "king" }
        "defend_card": { "suit": "spades", "rank": "qeen" }
    }
    {
        "action": "update_player",
        "user_id": "sasach69",
        "cards": { "suit": "spades", "rank": "king" }
    }
    ```
    """
    current_game = next((game for game in games if game.game_id == game_id), None)
    logging.debug(f"New connection: game_id={game_id}, user_id={player_id}")
    await manager.connect(websocket)
    try:
        if (
            current_game is not None
            and current_game.status == Game.GameStatus.GAME_FORMING
            and player_id not in current_game.players
        ):
            new_player = Game.Player("nick" + player_id, player_id)
            if current_game.add_player(new_player):
                await manager.send_personal_message(
                    json.dumps({"connection": "accept", "player": msgspec.to_builtins(current_game.players)}),
                    websocket=websocket
                )
                await manager.broadcast(  # бродкаст надо делать только тем, кто в текущей игре
                    json.dumps({"type": "update", "player": msgspec.to_builtins([new_player])}),
                    except_sender=websocket
                )
            else:
                logging.debug("Game is full")
                await manager.send_personal_message(
                    json.dumps({"connection": "denied", "reason": "fullRoom"}),
                    websocket=websocket
                )
                # manager.disconnect(websocket)
                raise WebSocketDisconnect()
        async for data in websocket.iter_text():
            logging.debug(data)
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        if (
            current_game
            and (current_game.status == Game.GameStatus.GAME_FORMING)
        ):
            logging.debug("Game is closing")
            current_game.remove_player(player_id)
            logging.debug(current_game.players)
        manager.disconnect(websocket)
    finally:
        current_game.remove_player(player_id)
        logging.debug(f"Connection closed: game_id={game_id}, user_id={player_id}")
        if websocket in manager.active_connections:
            manager.disconnect(websocket)


@app.post("/create_game/{player_id}")
async def create_game(player_id: str, request: Request):
    body = await request.json()
    game_iden = len(games) + 1
    games.append(
        Game.GameState(
            players=[],
            game_id=game_iden,
            room_size=body.get("room_size"),
            status=Game.GameStatus.GAME_FORMING,
            ))
    return {"game_id": game_iden}


@app.get("/games_list")  # тут сериализовать + websocket ?
async def games_list():
    json_compatible = []
    for game in games:
        # Базовое преобразование
        game_dict = msgspec.to_builtins(game)
        # Модификация данных
        json_compatible.append({
            "game_id": game_dict["game_id"],
            "room_size": game_dict["room_size"],
            "password": bool(game_dict.get("password")),
            "players": len(game_dict["players"]),
        })
    return json_compatible
# @app.websocket("/ws/{game_id}")
# async def websocket_endpoint(websocket: WebSocket, game_id: int):
#     await websocket.accept()
#     if game_id not in connections:
#         connections[game_id] = []
#     connections[game_id].append(websocket)

#     try:
#         while True:
#             data = await websocket.receive_text()
#             data_json = json.loads(data)
            
#             # Отправляем сообщение всем клиентам в этой игре
#             for connection in connections[game_id]:
#                 await connection.send_text(data)
    
#     except WebSocketDisconnect:
#         connections[game_id].remove(websocket)
#         if not connections[game_id]:
#             del connections[game_id]


# # Тестинг старта игры
# @app.get("/")
# async def game() -> list[str] | int:
#     player1: Game.Player = Game.Player(
#         _nickname="ss",
#         _identifier="$$as222",
#     )
#     logging.debug(player1)
#     player2: Game.Player = Game.Player(
#         _nickname="PU$$BOY",
#         _identifier="sakf4p32t35",
#     )
#     player3: Game.Player = Game.Player(
#         _nickname="YAEBAL",
#         _identifier="asfjkg403",
#     )
#     players: list = []
#     games: list = []
#     players.append(player1)
#     players.append(player2)
#     players.append(player3)
#     tst = msgspec.json.encode(player1)
#     logging.debug(tst)
#     msgspec.json.decode(tst, type=Game.Player)
#     print(player1.status)
#     games.append(game := Game.GameState(
#         3,
#         players=players,
#         ))
#     game.start_game()
#     logging.debug(games[0])

#     return 0
