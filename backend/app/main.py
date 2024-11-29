from typing import Optional, List, Self  # type: ignore
import logging
# import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
# from fastapi.staticfiles import StaticFiles
import redis.asyncio as asyncredis
import asyncpg  # type: ignore
import msgspec

import app.module.database.game_interface as Game

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
    print(a, b)
    value = await redis.get("foo")
    # value2 = redis.get("bar")

    # redis.execute()
    return {"Redis Value": value}


games = []
players = [int | None]  # cringe
gameiii = Game.GameState()
a = gameiii.start_game()
logging.debug(len(gameiii.deck_cards))
logging.debug(gameiii.deck_cards)
logging.debug(gameiii.trump_card)


@app.get("/game")
async def game() -> List[str] | int:
    player1: Game.Player = Game.Player(nickname=[], identifier="as2223ee", 
                                       __cards=[],
                                       condition=Game.PlayerStatus.READY)
    player2 = Game.Player(nickname="tojick", identifier="sad123asga",
                          __cards=[],
                          condition=Game.PlayerStatus.READY)
    player3 = Game.Player(nickname="uzbek", identifier="as2asd122s",
                          __cards=[],
                          condition=Game.PlayerStatus.READY)
    players.append(player1)
    players.append(player2)
    players.append(player3)
    tst = msgspec.json.encode(player1)
    msgspec.json.decode(tst, type=Game.Player)
    # print (player1.condition)
    games.append(game := Game.GameState(players=[player1],
                                        status=Game.GameStatus))
    a = game.start_game()
    logging.debug(len(a.deck_cards))

    return 0
