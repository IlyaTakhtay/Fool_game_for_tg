import asyncio
import logging

from dishka import FromDishka
from fastapi import WebSocket

from backend.src.api.managers.connection_managaer import ConnectionManager
from backend.src.api.managers.game_manager import GameManager
from backend.src.api.models.websocket.responses import (
    GameOverResponse,
    PlayerGameStateResponse,
)
from backend.src.api.models.websocket.data import GameOverData
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
from backend.src.game.models.player import Player
from backend.src.game.states.game_over import GameOverState
from backend.src.game.utils.errors import GameLogicError, WrongTurnError
from backend.src.game.config.settings import DEBUG

logger = logging.getLogger(__name__)


async def websocket_inout_resolve(
    message: IncomingMessage,
    game_id: str,
    player_id: str,
    game: FoolGame,
    websocket: WebSocket,
    cm: FromDishka[ConnectionManager],
    gm: FromDishka[GameManager],
) -> None:
    """
    Определяет тип входящего WebSocket сообщения и вызывает соответствующий обработчик.

    Args:
        message: Валидированное Pydantic-сообщение от клиента.
        game_id: ID текущей игры.
        player_id: ID игрока, отправившего сообщение.
        game: Экземпляр текущей игры.
        websocket: Экземпляр WebSocket соединения.
        cm: Экземпляр менеджера соединений.
        gm: Экземпляр менеджера игр.
    """
    logger.info(
        f"Получено сообщение от {player_id} в игре {game_id}: тип={message.type}"
    )

    match message.type:
        case "player_connected":
            await handle_player_connected(game_id, player_id, game, websocket, cm, gm)
        case "player_disconnected":
            await handle_player_disconnected(game_id, player_id, game, cm, gm)
        case "change_status":
            if isinstance(message, ChangeStatusRequest):
                await handle_player_status_changed(
                    game_id, player_id, message.data.status, game, cm, gm
                )
        case "play_card":
            if isinstance(message, PlayCardRequest):
                await handle_play_card(game_id, player_id, game, message, cm, gm)
        case "pass_turn":
            await handle_pass_turn(game_id, player_id, game, cm, gm)
        case "quit_game":
            await handle_quit_game(game_id, player_id, game, cm, gm)
        case _:
            logger.warning(f"Неизвестный тип сообщения: {message.type}")


async def reset_to_lobby_after_delay(
    game: FoolGame,
    delay: int,
    cm: FromDishka[ConnectionManager],
    gm: FromDishka[GameManager],
):
    """
    Сбрасывает игру в лобби после заданной задержки.

    Args:
        game: Экземпляр игры для сброса.
        delay: Задержка в секундах.
        cm: Экземпляр менеджера соединений.
        gm: Экземпляр менеджера игр.
    """
    await asyncio.sleep(delay)
    if game:
        logger.info(
            f"АВТО-СБРОС: Игра {game.game_id} возвращается в лобби через {delay} сек."
        )
        game.reset_to_lobby()
        await gm.save_game(game)
        await gm.publish_game_state_changed_event(game)


async def _handle_state_transition(
    game: FoolGame,
    transition: StateTransition,
    cm: FromDishka[ConnectionManager],
    gm: FromDishka[GameManager],
):
    """
    Обрабатывает переход состояния игры, включая завершение игры.

    Args:
        game: Экземпляр текущей игры.
        transition: Объект, описывающий переход состояния.
        cm: Экземпляр менеджера соединений.
        gm: Экземпляр менеджера игр.
    """
    logger.info(f"Обработка перехода состояния в {transition.new_state}")

    if transition.new_state == "GameOverState":
        game_over_state = game._current_state
        if not isinstance(game_over_state, GameOverState):
            logger.error(
                f"Состояние {transition.new_state}, но тип объекта {type(game_over_state)}!"
            )
            await gm.save_game(game) # Save game state even if type is wrong
            await gm.publish_game_state_changed_event(game)
            return

        await gm.save_game(game) # Save game state after game over
        await gm.publish_game_over_event(
            game, game_over_state.winner_id, game_over_state.loser_ids
        )
        asyncio.create_task(reset_to_lobby_after_delay(game, 3, cm, gm))
    else:
        await gm.save_game(game) # Save game state for other transitions
        await gm.publish_game_state_changed_event(game)


async def handle_player_connected(
    game_id: str,
    player_id: str,
    game: FoolGame,
    websocket: WebSocket,
    cm: FromDishka[ConnectionManager],
    gm: FromDishka[GameManager],
):
    """
    Обрабатывает успешное подключение игрока к WebSocket.

    Args:
        game_id: ID текущей игры.
        player_id: ID подключившегося игрока.
        game: Экземпляр текущей игры.
        websocket: Экземпляр WebSocket соединения.
        cm: Экземпляр менеджера соединений.
        gm: Экземпляр менеджера игр.
    """
    player: Player = next((p for p in game.players if p.id_ == player_id), None)
    if not player:
        logger.warning(f"Игрок {player_id} не найден в игре {game_id}")
        return
    await gm.publish_game_state_changed_event(game)


async def handle_player_disconnected(
    game_id: str,
    player_id: str,
    game: FoolGame,
    cm: FromDishka[ConnectionManager],
    gm: FromDishka[GameManager],
):
    """
    Обрабатывает отключение игрока от WebSocket.

    Args:
        game_id: ID текущей игры.
        player_id: ID отключившегося игрока.
        game: Экземпляр текущей игры.
        cm: Экземпляр менеджера соединений.
        gm: Экземпляр менеджера игр.
    """
    # Больше не вызываем exit_game, чтобы не завершать игру.
    # Вместо этого, мы могли бы установить статус игрока на "отключен",
    # но пока просто транслируем состояние.

    logger.info(f"Игрок {player_id} временно отключился от игры {game_id}.")

    # Просто транслируем полное состояние игры всем оставшимся игрокам.
    # Это позволит им увидеть, что игрок отключился (если на фронтенде есть такая логика)
    # и корректно продолжить игру, когда он вернется.
    updated_game = await gm.get_game_by_id(game_id)
    if updated_game:
        await gm.save_game(updated_game)
        await gm.publish_game_state_changed_event(updated_game)


async def handle_player_status_changed(
    game_id: str,
    player_id: str,
    new_status: str,
    game: FoolGame,
    cm: FromDishka[ConnectionManager],
    gm: FromDishka[GameManager],
):
    """
    Обрабатывает изменение статуса игрока (например, 'готов').

    Args:
        game_id: ID текущей игры.
        player_id: ID игрока.
        new_status: Новый статус игрока.
        game: Экземпляр текущей игры.
        cm: Экземпляр менеджера соединений.
        gm: Экземпляр менеджера игр.
    """
    try:
        player: Player = game.get_player_by_id(player_id=player_id)
        if not player:
            logger.error(f"Игрок {player_id} не найден в игре {game_id}")
            return

        action = PlayerAction.READY if new_status == "ready" else PlayerAction.UNREADY
        response = game.handle_input(
            player_input=PlayerInput(player_id=player_id, action=action)
        )

        if isinstance(response, StateTransition):
            await _handle_state_transition(game, response, cm, gm)
            return

        if response.result != ActionResult.SUCCESS:
            raise GameLogicError(message=response.message, error_code="INVALID_ACTION")

        # Просто транслируем всем обновленное состояние
        await gm.save_game(game)
        await gm.publish_game_state_changed_event(game)

    except (GameLogicError, Exception) as e:
        logger.error(
            f"Ошибка при обработке изменения статуса игрока: {e}", exc_info=DEBUG
        )
        raise


async def handle_play_card(
    game_id: str,
    player_id: str,
    game: FoolGame,
    message: PlayCardRequest,
    cm: FromDishka[ConnectionManager],
    gm: FromDishka[GameManager],
):
    """
    Обрабатывает ход игрока картой.

    Args:
        game_id: ID текущей игры.
        player_id: ID игрока, совершающего ход.
        game: Экземпляр текущей игры.
        message: Валидированное Pydantic-сообщение с данными о картами.
        cm: Экземпляр менеджера соединений.
        gm: Экземпляр менеджера игр.
    """
    attack_card_data = message.data.attack_card
    defend_card_data = message.data.defend_card

    try:
        # Проверка роли игрока
        is_attacker = game.current_attacker_id == player_id
        is_defender = game.current_defender_id == player_id
        is_attack_action = not defend_card_data
        is_defense_action = bool(defend_card_data)

        if is_attack_action and not is_attacker:
            raise WrongTurnError("Сейчас не ваш ход для атаки", "WRONG_TURN")
        elif is_defense_action and not is_defender:
            raise WrongTurnError("Сейчас не ваш ход для защиты", "WRONG_TURN")

        # Создание объектов карт из данных
        trump_suit = game.deck.trump_suit
        attack_card = Card.from_dict(
            attack_card_data.model_dump(), trump_suit=trump_suit
        )
        defend_card = (
            Card.from_dict(defend_card_data.model_dump(), trump_suit=trump_suit)
            if defend_card_data
            else None
        )

        # Формирование действия игрока
        action = PlayerAction.DEFEND if defend_card else PlayerAction.ATTACK
        player_input = PlayerInput(
            player_id=player_id,
            action=action,
            attack_card=attack_card,
            defend_card=defend_card,
        )

        # Обработка действия в ядре игры
        answer = game.handle_input(player_input)

        if isinstance(answer, StateTransition):
            await _handle_state_transition(game, answer, cm, gm)
        elif (
            isinstance(answer, StateResponse) and answer.result == ActionResult.SUCCESS
        ):
            await gm.save_game(game)
            await gm.publish_game_state_changed_event(game)
        else:
            raise GameLogicError(answer.message, "PLAY_CARD_ERROR")

    except (ValueError, KeyError, TypeError) as e:
        raise GameLogicError(f"Неверный формат карты: {e}", "INVALID_CARD_FORMAT")
    except (GameLogicError, WrongTurnError) as e:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обработке хода: {e}", exc_info=DEBUG)
        raise GameLogicError(
            f"Ошибка при обработке хода: {e}", "UNEXPECTED_PLAY_CARD_ERROR"
        )


async def handle_pass_turn(
    game_id: str,
    player_id: str,
    game: FoolGame,
    cm: FromDishka[ConnectionManager],
    gm: FromDishka[GameManager],
):
    """
    Обрабатывает действие "пас" от игрока.

    Args:
        game_id: ID текущей игры.
        player_id: ID игрока, который пасует.
        game: Экземпляр текущей игры.
        cm: Экземпляр менеджера соединений.
        gm: Экземпляр менеджера игр.
    """
    try:
        player_input = PlayerInput(player_id=player_id, action=PlayerAction.PASS)
        answer = game.handle_input(player_input)

        if isinstance(answer, StateTransition):
            await _handle_state_transition(game, answer, cm, gm)
        elif (
            isinstance(answer, StateResponse) and answer.result == ActionResult.SUCCESS
        ):
            await gm.save_game(game)
            await gm.publish_game_state_changed_event(game)
        else:
            raise GameLogicError(answer.message, "PASS_TURN_ERROR")
    except (GameLogicError, Exception) as e:
        logger.error(
            f"Ошибка в handle_pass_turn для игрока {player_id}: {e}", exc_info=DEBUG
        )
        raise


async def handle_quit_game(
    game_id: str,
    player_id: str,
    game: FoolGame,
    cm: FromDishka[ConnectionManager],
    gm: FromDishka[GameManager],
):
    """
    Обрабатывает выход игрока из игры.

    Args:
        game_id: ID текущей игры.
        player_id: ID игрока, который выходит.
        game: Экземпляр текущей игры.
        cm: Экземпляр менеджера соединений.
        gm: Экземпляр менеджера игр.
    """
    try:
        response = game.handle_input(
            PlayerInput(player_id=player_id, action=PlayerAction.QUIT)
        )

        if len(game.players) == 0:
            await gm.delete_game(game.game_id)
            await gm._sm.delete_queue(player_id) # Delete queue when player quits and game is empty
            logger.info(f"Игра {game.game_id} удалена, так как последний игрок вышел.")
            return

        if isinstance(response, StateTransition):
            await _handle_state_transition(game, response, cm, gm)
        else:
            # В случае, если не произошел переход состояния, просто обновим всех
            await gm.save_game(game)
            await gm.publish_game_state_changed_event(game)
        
        await gm._sm.delete_queue(player_id) # Delete queue when player quits


    except (GameLogicError, Exception) as e:
        logger.error(
            f"Ошибка в handle_quit_game для игрока {player_id}: {e}", exc_info=DEBUG
        )
        # В случае ошибки можно дополнительно уведомить игрока
        raise
