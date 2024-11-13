# import typing
import logging
# import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
# from fastapi.staticfiles import StaticFiles
import redis.asyncio as asyncredis
import asyncpg  # type: ignore
import msgspec

from .module.database.database_interface import (
    GameState,
    TableState,
    Player,
    Trump_Card,
    Card,
    GameStatus,
    PlayerStatus)  # type: ignore

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


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/")
async def read_root():
    a = await redis.set("foo", "bar")
    b = await redis.set("bar", "foo")

    value = await redis.get("foo")
    # value2 = redis.get("bar")

    # redis.execute()
    return {"Redis Value": value}


games = []
players = [int | None]  # cringe


@app.get("/game")
async def game():
    player1 = Player(nickname=[], identifier="as2223ee", cards=[],
                     condition=PlayerStatus.READY)
    player2 = Player(nickname="tojick", identifier="sad123asga", cards=[],
                     condition=PlayerStatus.READY)
    player3 = Player(nickname="uzbek", identifier="as2asd122s", cards=[],
                     condition=PlayerStatus.READY)
    players.append(player1)
    players.append(player2)
    players.append(player3)
    tst = msgspec.json.encode(player1)
    msgspec.json.decode(tst, type=Player)
    # print (player1.condition)
    games.append(game := GameState(players=[].append(player1),
                                   status=GameStatus))
    a = game.start_game()
    logging.debug(a)


    return 0
