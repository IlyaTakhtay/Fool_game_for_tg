import time
import msgspec.msgpack
from redis.asyncio import Redis
from typing import Dict, Any, List
import logging
from backend.src.adapters.persistence.redis import RedisFoolGameAdapter
from backend.src.storage.repositories.interfaces import IGameRepository
from backend.src.game.models.game import FoolGame

logger = logging.getLogger(__name__)


class RedisGameRepository(IGameRepository):
    def __init__(self, client: Redis):
        self.client: Redis = client

    async def get_by_id(self, game_id: str) -> FoolGame | None:
        """Получить игру по ID"""
        data = await self.client.get(f"game:{game_id}")
        if not data:
            return None
        try:
            return RedisFoolGameAdapter.decode(data)
        except Exception as e:
            logger.error(f"Failed to decode game {game_id}: {e}")
            return None

    async def save(self, game: FoolGame) -> None:
        """Сохранить игру с автоматической индексацией"""
        old_game = await self.get_by_id(game.game_id)
        old_player_ids = {p.id_ for p in old_game.players} if old_game else set()
        current_player_ids = {p.id_ for p in game.players}

        # encoded = self.encoder.encode(game.to_dict())
        encoded = RedisFoolGameAdapter.encode(game)
        async with self.client.pipeline(transaction=False) as pipe:
            pipe.set(f"game:{game.game_id}", encoded)

            if old_game and old_game.status != game.status:
                pipe.zrem(f"games:status:{old_game.status}", game.game_id)
            pipe.zadd(f"games:status:{game.status}", {game.game_id: 0})

            pipe.delete(f"game:{game.game_id}:players")
            if current_player_ids:
                pipe.sadd(f"game:{game.game_id}:players", *current_player_ids)

            removed_players = old_player_ids - current_player_ids
            for player_id in removed_players:
                pipe.delete(f"player:{player_id}:game")

            for player_id in current_player_ids:
                pipe.set(f"player:{player_id}:game", game.game_id)

            await pipe.execute()

    async def delete(self, game_id: str) -> None:
        """Удалить игру атомарно"""
        game = await self.get_by_id(game_id)
        if not game:
            return

        player_ids = {p.id_ for p in game.players} if game else set()

        async with self.client.pipeline(transaction=False) as pipe:
            pipe.delete(f"game:{game_id}")
            pipe.zrem("games:status:pending", game_id)
            pipe.zrem("games:status:active", game_id)
            pipe.zrem("games:status:finished", game_id)

            for player_id in player_ids:
                pipe.delete(f"player:{player_id}:game")

            await pipe.execute()

    async def find_by_status(
        self, status: str, limit: int = 100, offset: int = 0
    ) -> List[FoolGame]:
        """Найти игры по статусу"""
        game_ids = await self.client.zrange(
            f"games:status:{status}", offset, offset + limit - 1
        )

        if not game_ids:
            return []

        async with self.client.pipeline(transaction=False) as pipe:
            for game_id in game_ids:
                decoded_id = self._decode_bytes(game_id)
                pipe.get(f"game:{decoded_id}")
            results = await pipe.execute()

        games = []
        for data in results:
            if data:
                try:
                    game = RedisFoolGameAdapter.decode(data)
                    games.append(game)
                except Exception as e:
                    logger.error(f"Failed to decode game: {e}")

        return games

    async def find_by_player_id(self, player_id: str) -> FoolGame | None:
        """Найти игру игрока"""
        game_id_raw = await self.client.get(f"player:{player_id}:game")

        if not game_id_raw:
            return None

        return await self.get_by_id(self._decode_bytes(game_id_raw))

    def _decode_bytes(self, value: bytes | str) -> str:
        """Декодировать bytes в str"""
        return value.decode("utf-8") if isinstance(value, bytes) else value
