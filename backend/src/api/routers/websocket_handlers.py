import asyncio
import logging
from typing import Callable, Awaitable

from dishka import FromDishka
from fastapi import WebSocket

from backend.src.api.managers.game_manager import GameManager
from backend.src.api.models.websocket.requests import (
    IncomingMessage,
    PlayCardRequest,
    ChangeStatusRequest,
)
from backend.src.game.contracts.game_contract import (
    ActionResult,
    PlayerAction,
    PlayerInput,
    StateResponse,
    StateTransition,
)
from backend.src.game.models.card import Card
from backend.src.game.models.game import FoolGame
from backend.src.game.states.game_over import GameOverState
from backend.src.game.utils.errors import GameLogicError, WrongTurnError

logger = logging.getLogger(__name__)


class MessageRouter:
    """Роутер для WebSocket сообщений"""

    _handlers: dict[str, Callable[..., Awaitable[None]]] = {}

    @classmethod
    def register(cls, message_type: str):
        """Декоратор для регистрации обработчика"""

        def decorator(
            func: Callable[..., Awaitable[None]],
        ) -> Callable[..., Awaitable[None]]:
            cls._handlers[message_type] = func
            logger.debug(
                f"Зарегистрирован обработчик '{func.__name__}' для '{message_type}'"
            )
            return func

        return decorator

    @classmethod
    async def route(
        cls,
        message: IncomingMessage,
        player_id: str,
        game: FoolGame,
        gm: GameManager,
    ):
        """Маршрутизирует сообщение к обработчику"""
        logger.info(
            f"Получено сообщение от {player_id} в игре {game.game_id}: тип={message.type}"
        )

        handler = cls._handlers.get(message.type)

        if handler:
            await handler(player_id, game, message, gm)
        else:
            logger.warning(f"Неизвестный тип сообщения: {message.type}")


async def websocket_inout_resolve(
    message: IncomingMessage,
    game_id: str,
    player_id: str,
    game: FoolGame,
    gm: FromDishka[GameManager],
) -> None:
    """Маршрутизирует WebSocket сообщения через роутер."""

    await MessageRouter.route(message, player_id, game, gm)


async def reset_to_lobby_after_delay(
    game: FoolGame,
    delay: int,
    gm: GameManager,
):
    """Сбрасывает игру в лобби после заданной задержки."""
    try:
        await asyncio.sleep(delay)
        if game:
            logger.info(
                f"Сброс игры: Игра {game.game_id} возвращается в лобби через {delay} сек."
            )
            game.reset_to_lobby()
            await gm.save_game(game)
            await gm.publish_full_game_state(game)
    except Exception as e:
        logger.error(f"Ошибка в авто-сбросе игры {game.game_id}: {e}", exc_info=True)


async def _handle_state_transition(
    game: FoolGame,
    transition: StateTransition,
    gm: GameManager,
):
    """Обрабатывает переход состояния игры, включая завершение игры."""
    logger.info(f"Обработка перехода состояния в {transition.new_state}")

    await gm.save_game(game)

    if transition.new_state == "GameOverState":
        now_state = game._current_state
        if not isinstance(now_state, GameOverState):
            logger.error(
                f"Ожидалось состояние GameOverState, но получен {type(now_state)}!"
            )
            await gm.publish_full_game_state(game)
            return

        await gm.publish_game_over_event(game, now_state.winner_id, now_state.loser_ids)

        asyncio.create_task(reset_to_lobby_after_delay(game, 3, gm))
    else:
        await gm.publish_full_game_state(game)


@MessageRouter.register("change_status")
async def handle_player_status_changed(
    player_id: str,
    game: FoolGame,
    message: ChangeStatusRequest,
    gm: GameManager,
):
    """Обрабатывает изменение статуса игрока."""
    new_status = message.data.status
    action = PlayerAction.READY if new_status == "ready" else PlayerAction.UNREADY
    response = game.handle_input(PlayerInput(player_id=player_id, action=action))

    if isinstance(response, StateTransition):
        await _handle_state_transition(game, response, gm)
        return

    if response.result != ActionResult.SUCCESS:
        raise GameLogicError(message=response.message, error_code="INVALID_ACTION")

    await gm.save_game(game)
    await gm.publish_full_game_state(game)


@MessageRouter.register("play_card")
async def handle_play_card(
    player_id: str,
    game: FoolGame,
    message: PlayCardRequest,
    gm: GameManager,
):
    """Обрабатывает ход игрока картой."""
    attack_card_data = message.data.attack_card
    defend_card_data = message.data.defend_card

    # Проверка роли игрока
    is_attacker = game.current_attacker_id == player_id
    is_defender = game.current_defender_id == player_id
    is_attack_action = not defend_card_data

    if is_attack_action and not is_attacker:
        raise WrongTurnError("Сейчас не ваш ход для атаки", "WRONG_TURN")
    elif not is_attack_action and not is_defender:
        raise WrongTurnError("Сейчас не ваш ход для защиты", "WRONG_TURN")

    # Создание объектов карт
    trump_suit = game.deck.trump_suit
    attack_card = Card.from_dict(attack_card_data.model_dump(), trump_suit=trump_suit)
    defend_card = (
        Card.from_dict(defend_card_data.model_dump(), trump_suit=trump_suit)
        if defend_card_data
        else None
    )

    # Формирование действия
    action = PlayerAction.DEFEND if defend_card else PlayerAction.ATTACK
    player_input = PlayerInput(
        player_id=player_id,
        action=action,
        attack_card=attack_card,
        defend_card=defend_card,
    )

    # Обработка действия
    answer = game.handle_input(player_input)

    if isinstance(answer, StateTransition):
        await _handle_state_transition(game, answer, gm)
    elif isinstance(answer, StateResponse) and answer.result == ActionResult.SUCCESS:
        await gm.save_game(game)
        await gm.publish_full_game_state(game)
    else:
        raise GameLogicError(answer.message, "PLAY_CARD_ERROR")


@MessageRouter.register("pass_turn")
async def handle_pass_turn(
    player_id: str,
    game: FoolGame,
    message: IncomingMessage,
    gm: GameManager,
):
    """Обрабатывает действие "пас" от игрока."""
    player_input = PlayerInput(player_id=player_id, action=PlayerAction.PASS)
    answer = game.handle_input(player_input)

    if isinstance(answer, StateTransition):
        await _handle_state_transition(game, answer, gm)
    elif isinstance(answer, StateResponse) and answer.result == ActionResult.SUCCESS:
        await gm.save_game(game)
        await gm.publish_full_game_state(game)
    else:
        raise GameLogicError(answer.message, "PASS_TURN_ERROR")


@MessageRouter.register("quit_game")
async def handle_quit_game(
    player_id: str,
    game: FoolGame,
    message: IncomingMessage,
    gm: GameManager,
):
    """Обрабатывает полный выход игрока из игры (не дисконнект)."""
    await gm.exit_game(player_id)
