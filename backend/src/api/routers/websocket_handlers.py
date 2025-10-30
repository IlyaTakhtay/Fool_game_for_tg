import asyncio
import logging

from dishka import FromDishka
from fastapi import WebSocket

from backend.src.api.managers.connection_managaer import ConnectionManager
from backend.src.api.managers.game_manager import GameManager
from backend.src.api.models.websocket_models import (
    GameOverData,
    GameOverResponse,
    PlayerDisconnectedData,
    PlayerDisconnectedResponse,
    PlayerStatusChangedResponse,
    PlayerStatusData,
    PublicPlayerData,
    ReconnectionData,
    ReconnectionResponse,
    SelfStatusUpdateData,
    SelfStatusUpdateResponse,
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
from backend.src.game.models.player import Player, PlayerStatus
from backend.src.game.states.game_over import GameOverState
from backend.src.game.utils.errors import GameLogicError, WrongTurnError
from backend.src.game.config.settings import DEBUG

logger = logging.getLogger(__name__)


async def websocket_inout_resolve(
    data: dict,
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
        data: Данные, полученные от клиента.
        game_id: ID текущей игры.
        player_id: ID игрока, отправившего сообщение.
        game: Экземпляр текущей игры.
        websocket: Экземпляр WebSocket соединения.
        cm: Экземпляр менеджера соединений.
        gm: Экземпляр менеджера игр.
    """
    message_type = data.get("type")
    message_data = data.get("data")
    logger.info(
        f"Получено сообщение от {player_id} в игре {game_id}: тип={message_type}"
    )

    match message_type:
        case "player_connected":
            await handle_player_connected(game_id, player_id, game, websocket, cm, gm)
        case "player_disconnected":
            await handle_player_disconnected(game_id, player_id, game, cm, gm)
        case "change_status":
            new_status = message_data.get("status")
            await handle_player_status_changed(
                game_id, player_id, new_status, game, cm, gm
            )
        case "play_card":
            await handle_play_card(game_id, player_id, game, websocket, data, cm, gm)
        case "pass_turn":
            await handle_pass_turn(game_id, player_id, game, cm, gm)
        case "quit_game":
            await handle_quit_game(game_id, player_id, game, cm, gm)
        case _:
            logger.warning(f"Неизвестный тип сообщения: {message_type}")


async def _broadcast_full_game_state(game: FoolGame, cm: ConnectionManager):
    """
    Транслирует полное состояние игры всем игрокам в комнате.

    Args:
        game: Экземпляр текущей игры.
        cm: Экземпляр менеджера соединений.
    """
    all_allowed_actions = game.get_allowed_actions()

    for p in game.players:
        player_actions = all_allowed_actions.get(p.id_, [])
        full_state_response = ReconnectionResponse(
            data=ReconnectionData(
                current_state=game.current_state_name,
                status=p.status,
                position=game.get_player_position(p.id_),
                cards=[card.to_dict() for card in p.get_cards()],
                allowed_actions=player_actions,
                room_size=game.players_limit,
                room_players=[
                    PublicPlayerData(
                        player_id=other_p.id_,
                        position=game.get_player_position(other_p.id_),
                        cards_count=len(other_p.get_cards()),
                        status=getattr(other_p, "status", PlayerStatus.UNREADY),
                        name=other_p.name,
                    )
                    for other_p in game.players
                    if other_p.id_ != p.id_
                ],
                deck_size=len(game.deck),
                trump_suit=game.deck.trump_suit if game.deck.trump_suit else None,
                trump_rank=game.deck.trump_card.rank if game.deck.trump_card else None,
                attacker_position=(
                    game.get_player_position(game.current_attacker_id)
                    if game.current_attacker_id
                    else -1
                ),
                defender_position=(
                    game.get_player_position(game.current_defender_id)
                    if game.current_defender_id
                    else -1
                ),
                table_cards=[
                    {
                        "attack_card": (
                            pair.get("attack_card").to_dict()
                            if pair.get("attack_card")
                            else None
                        ),
                        "defend_card": (
                            pair.get("defend_card").to_dict()
                            if pair.get("defend_card")
                            else None
                        ),
                    }
                    for pair in game.game_table.table_cards
                ],
            )
        )
        await cm.send_message(p.id_, full_state_response.model_dump())


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
        await _broadcast_full_game_state(game, cm)


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
            await _broadcast_full_game_state(game, cm)
            return

        game_over_response = GameOverResponse(
            data=GameOverData(
                winner_id=game_over_state.winner_id,
                loser_ids=game_over_state.loser_ids,
            )
        )
        all_player_ids = [p.id_ for p in game.players]
        await cm.broadcast_to_players(all_player_ids, game_over_response.model_dump())
        asyncio.create_task(reset_to_lobby_after_delay(game, 3, cm, gm))
    else:
        await _broadcast_full_game_state(game, cm)


async def _send_full_game_state_to_player(
    game: FoolGame,
    player_id: str,
    cm: FromDishka[ConnectionManager],
):
    """
    Отправляет полное состояние игры конкретному игроку.

    Args:
        game: Экземпляр текущей игры.
        player_id: ID игрока, которому отправляется состояние.
        cm: Экземпляр менеджера соединений.
    """
    player = game.get_player_by_id(player_id)
    if not player:
        logger.warning(
            f"Попытка отправить состояние несуществующему игроку {player_id}"
        )
        return

    all_allowed_actions = game.get_allowed_actions()
    player_actions = all_allowed_actions.get(player.id_, [])

    full_state_response = ReconnectionResponse(
        data=ReconnectionData(
            current_state=game.current_state_name,
            status=player.status,
            position=game.get_player_position(player.id_),
            cards=[card.to_dict() for card in player.get_cards()],
            allowed_actions=player_actions,
            room_size=game.players_limit,
            room_players=[
                PublicPlayerData(
                    player_id=other_p.id_,
                    position=game.get_player_position(other_p.id_),
                    cards_count=len(other_p.get_cards()),
                    status=getattr(other_p, "status", PlayerStatus.UNREADY),
                    name=other_p.name,
                )
                for other_p in game.players
                if other_p.id_ != player.id_
            ],
            deck_size=len(game.deck),
            trump_suit=game.deck.trump_suit,
            trump_rank=game.deck.trump_card.rank if game.deck.trump_card else None,
            attacker_position=(
                game.get_player_position(game.current_attacker_id)
                if game.current_attacker_id
                else -1
            ),
            defender_position=(
                game.get_player_position(game.current_defender_id)
                if game.current_defender_id
                else -1
            ),
            table_cards=[
                {
                    "attack_card": (
                        pair.get("attack_card").to_dict()
                        if pair.get("attack_card")
                        else None
                    ),
                    "defend_card": (
                        pair.get("defend_card").to_dict()
                        if pair.get("defend_card")
                        else None
                    ),
                }
                for pair in game.game_table.table_cards
            ],
        )
    )
    await cm.send_message(player.id_, full_state_response.model_dump())


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
    await _broadcast_full_game_state(game, cm)


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
        await _broadcast_full_game_state(updated_game, cm)


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

        all_allowed_actions = game.get_allowed_actions()
        player_actions = all_allowed_actions.get(player_id, [])
        self_update_response = SelfStatusUpdateResponse(
            data=SelfStatusUpdateData(status=new_status, allowed_actions=player_actions)
        )
        await cm.send_message(player_id, self_update_response.model_dump())

        status_response = PlayerStatusChangedResponse(
            data=PlayerStatusData(player_id=player_id, status=new_status)
        )
        other_player_ids = [p.id_ for p in game.players if p.id_ != player_id]
        if other_player_ids:
            await cm.broadcast_to_players(
                other_player_ids, status_response.model_dump()
            )

    except (GameLogicError, Exception) as e:
        logger.error(
            f"Ошибка при обработке изменения статуса игрока: {e}", exc_info=DEBUG
        )
        raise


async def handle_play_card(
    game_id: str,
    player_id: str,
    game: FoolGame,
    websocket: WebSocket,
    data: dict,
    cm: FromDishka[ConnectionManager],
    gm: FromDishka[GameManager],
):
    """
    Обрабатывает ход игрока картой.

    Args:
        game_id: ID текущей игры.
        player_id: ID игрока, совершающего ход.
        game: Экземпляр текущей игры.
        websocket: Экземпляр WebSocket соединения.
        data: Данные, содержащие информацию о картах.
        cm: Экземпляр менеджера соединений.
        gm: Экземпляр менеджера игр.
    """
    attack_card_data = data.get("attack_card")
    if not attack_card_data:
        raise GameLogicError("Не указана карта для хода", "CARD_REQUIRED")

    defend_card_data = data.get("defend_card")

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
        attack_card = Card.from_dict(attack_card_data, trump_suit=trump_suit)
        defend_card = (
            Card.from_dict(defend_card_data, trump_suit=trump_suit)
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
            await _broadcast_full_game_state(game, cm)
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
            await _broadcast_full_game_state(game, cm)
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
            logger.info(f"Игра {game.game_id} удалена, так как последний игрок вышел.")
            return

        if isinstance(response, StateTransition):
            await _handle_state_transition(game, response, cm, gm)
        else:
            # В случае, если не произошел переход состояния, просто обновим всех
            await _broadcast_full_game_state(game, cm)

    except (GameLogicError, Exception) as e:
        logger.error(
            f"Ошибка в handle_quit_game для игрока {player_id}: {e}", exc_info=DEBUG
        )
        # В случае ошибки можно дополнительно уведомить игрока
        raise
