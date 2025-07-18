from __future__ import annotations
import logging
from typing import Dict, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.models.game import FoolGame

from backend.app.models.card import Card
from backend.app.utils.game_interface import GameState
from backend.app.models.player import Player, PlayerStatus
from backend.app.contracts.game_contract import (
    PlayerInput,
    PlayerAction,
    ActionResult,
    StateResponse,
    StateTransition,
)

logger = logging.getLogger(__name__)


class ExtraThrowActionMixin:
    def _extra_throw_action(self, player_input) -> ActionResult:
        if (
            player_input.action == PlayerAction.PASS
            and player_input.player_id == self.game.current_attacker_id
        ):
            # Пока защищающийся игрок не нажал COLLECT или не покрыл все карты, отправляем INVALID ACTION
            if (
                not self._is_all_cards_defended()
                or self.round_defender_status == PlayerAction.COLLECT
            ):
                return StateResponse(
                    ActionResult.INVALID_ACTION,
                    "Нельзя пасовать, пока защищающийся не отбил все карты или не пасанул сам",
                )
            else:
                # TODO: сделать так, чтобы это было только ПРИ ИГРЕ С ПОДБРАСЫВАНИЕМ
                sorted_players: List[Player] = list(
                    self.game.players[self.game.current_defender_idx + 1 :]
                    + self.game.players[: self.game.current_defender_idx]
                )
                next_attacker: Player = next(
                    (
                        p
                        for p in sorted_players
                        if p.status == PlayerStatus.READY
                        and p.status != PlayerStatus.VICTORY
                    ),
                    None,
                )
                if next_attacker:
                    self.game.current_attacker_idx = (
                        self.game.current_attacker_idx + 1
                    ) % len(self.game.players)
                    self.game.current_attacker_id = next_attacker
                    return StateResponse(
                        result=ActionResult.SUCCESS,
                        message=f"Ход игрока {player_input.player_id} пропущен. Ход переходит игроку {next_attacker.name}",
                        next_state="DealState",
                        data={"table": self.game.game_table.table_cards},
                    )
                else:
                    return StateResponse(
                        result=ActionResult.SUCCESS,
                        message=f"Последний закончил ход игрок {player_input.player_id}",
                        next_state="DealState",
                        data={"table": self.game.game_table.table_cards},
                    )


class PlayRoundWithoutThrowState(GameState):
    """Состояние проигрыша раунда в игре Дурак, для игры без подбрасывания"""

    def __init__(self, game: FoolGame) -> None:
        self.game: FoolGame = game

    def enter(self) -> Dict[str, Any]:
        """
        Инициализирует состояние атаки

        Returns:
            Dict[str, Any]: Информация о входе в состояние атаки
        """

        # Очищаем игровой стол и статус раунда перед новым раундом
        self.game.game_table.clear_table()
        self.game.round_defender_status = None

        return {
            "message": f"Ход игрока {self.game.current_attacker_id}. Выберите карту для атаки.",
            "attacker_id": self.game.current_attacker_id,
            "defender_id": self.game.current_defender_id,
            "table_cards": [],
        }

    def exit(self) -> Dict[str, Any]:
        """
        Вызывается при выходе из состояния атаки

        Returns:
            Dict[str, Any]: Информация о результатах состояния
        """
        if self.game.round_defender_status == PlayerAction.DEFEND:
            # TODO: убрать константу
            self.game.game_table.slots = 6

        # Отдаем в руку карты со стола игроку, который не отбился
        if self.game.round_defender_status == PlayerAction.COLLECT:
            for pair in self.game.game_table.table_cards:
                for card in pair.items():
                    pl: Player = self.game.players[self.game.current_defender_idx]
                    if pl:
                        pl.add_card(card)
        logging.debug(f"current defender status is{self.game.round_defender_status}")
        # self.game.game_table.clear_table()
        return {
            "message": "Драка завершена.",
            "table_cards": self.game.game_table.table_cards,
        }

    def handle_input(self, player_input: PlayerInput) -> StateResponse:
        """
        Обрабатывает ввод игрока в состоянии атаки
        """
        if player_input.action == PlayerAction.QUIT:
            return self._handle_player_quit_action(player_input)

        attacker_id = self.game.current_attacker_id
        defender_id = self.game.current_defender_id

        # --- Pre-action validation ---
        # Block any player who is not the current attacker or defender.
        if player_input.player_id not in [attacker_id, defender_id]:
            return StateResponse(ActionResult.NOT_YOUR_TURN, "Сейчас не ваш ход.")

        # If the defender has already decided to take cards, block any further actions from them.
        is_defender_collecting = self.game.round_defender_status == PlayerAction.COLLECT
        if is_defender_collecting and player_input.player_id == defender_id:
            return StateResponse(ActionResult.INVALID_ACTION, "Вы уже решили взять карты, ожидайте паса от атакующего.")

        # --- Actions of the Attacker ---
        if player_input.player_id == attacker_id:
            if player_input.action == PlayerAction.ATTACK:
                return self._check_attack_rules(player_input)

            if player_input.action == PlayerAction.PASS:
                if is_defender_collecting:
                    # Attacker is done with throw-ins. Defender takes all cards.
                    defender = self.game.get_player_by_id(defender_id)
                    cards_to_take = self.game.game_table.get_all_cards()
                    for card in cards_to_take:
                        defender.add_card(card)
                    self.game.game_table.clear_table()
                    
                    return StateResponse(
                        result=ActionResult.SUCCESS,
                        message=f"Атака завершена. Защищающийся {defender_id} забирает карты.",
                        next_state="DealState"
                    )
                else:
                    # Attacker passes, defender must have beaten all cards.
                    if not self._is_all_cards_defended():
                        return StateResponse(ActionResult.INVALID_ACTION, "Нельзя пасовать, пока защищающийся не отбил все карты.")
                    
                    self.game.round_defender_status = PlayerAction.DEFEND
                    self.game.game_table.clear_table()
                    return StateResponse(
                        result=ActionResult.SUCCESS,
                        message="Защищающийся отбился. Карты биты.",
                        next_state="DealState"
                    )
        
        # --- Actions of the Defender ---
        # We know the defender is not in 'collecting' state here due to the check above.
        if player_input.player_id == defender_id:
            if player_input.action == PlayerAction.DEFEND:
                return self._check_defend_rules(player_input)
            
            if player_input.action == PlayerAction.PASS:
                # Player cannot take cards if they have already beaten all of them.
                if self._are_all_cards_on_table_defended():
                    return StateResponse(
                        ActionResult.INVALID_ACTION,
                        "Вы отбили все карты. Ожидайте следующего хода атакующего или его паса."
                    )

                if not self.game.game_table.table_cards:
                    return StateResponse(ActionResult.INVALID_ACTION, "Нельзя пасовать, если на столе нет карт.")
                
                self.game.round_defender_status = PlayerAction.COLLECT
                return StateResponse(
                    result=ActionResult.SUCCESS,
                    message="Защищающийся решил взять карты. Атакующий может подкинуть."
                )

        # This part of the code should not be reachable due to the initial checks.
        return StateResponse(ActionResult.INVALID_ACTION, "Нераспознанное действие или неверный ход.")

    def _check_attack_rules(self, player_input: PlayerInput) -> StateResponse:
        # Проверка наличия карты для атаки
        if not player_input.attack_card:
            return StateResponse(
                ActionResult.CARD_REQUIRED, "Необходимо выбрать карту для атаки."
            )

        try:
            attacker: Player = self.game.players[self.game.current_attacker_idx]
        except (TypeError, IndexError):
            attacker = None
        if not attacker or player_input.attack_card not in attacker.get_cards():
            logger.info(f"Player hand: {[str(c) for c in attacker.get_cards()]}")
            logger.info(f"Card to play: {player_input.attack_card} (rank={player_input.attack_card.rank} id={id(player_input.attack_card.rank)} type={type(player_input.attack_card.rank)}), (suit={player_input.attack_card.suit} id={id(player_input.attack_card.suit)} type={type(player_input.attack_card.suit)})")
            for c in attacker.get_cards():
                logger.info(f"  Card in hand: {c} (rank={c.rank} id={id(c.rank)} type={type(c.rank)}), (suit={c.suit} id={id(c.suit)} type={type(c.suit)})")
                logger.info(f"    card == c: {player_input.attack_card == c}, card is c: {player_input.attack_card is c}, hash(card): {hash(player_input.attack_card)}, hash(c): {hash(c)}")
                logger.info(f"    card.rank module: {player_input.attack_card.rank.__module__}, c.rank module: {c.rank.__module__}")
                logger.info(f"    card.suit module: {player_input.attack_card.suit.__module__}, c.suit module: {c.suit.__module__}")
            return StateResponse(ActionResult.INVALID_CARD, "У вас нет такой карты.")

        result = self.game.game_table.throw_card(player_input.attack_card)

        # Проверяем правила подкидывания (если стол не пуст)
        if self.game.game_table.table_cards and result["status"] == "failed":
            if result["message"] == "no free slots":
                return StateResponse(ActionResult.TABLE_FULL, "Стол полный")
            if result["message"] == "wrong rank":
                return StateResponse(
                    ActionResult.WRONG_CARD,
                    "Эту карту нельзя подкинуть. Можно подкидывать только карты тех же достоинств, что уже есть на столе.",
                )

        # Проверка на то, что у игрока достаточно карт для защиты / взятия
        defender = self.game.get_player_by_id(self.game.current_defender_id)
        if defender:
            # If the defender is taking cards, the attacker can't throw in more cards than the defender has.
            if self.game.round_defender_status == PlayerAction.COLLECT:
                attack_cards_on_table = self.game.game_table._get_attack_cards()
                if len(attack_cards_on_table) >= len(defender.get_cards()):
                    return StateResponse(ActionResult.TABLE_FULL, "Нельзя подкинуть больше карт, чем есть у защищающегося.")
            # If the defender is still playing, they must have enough cards to beat the new attack.
            else:
                 if not self._is_defender_able_to_beat_more(defender_cards=defender.get_cards()):
                    return StateResponse(
                        ActionResult.TABLE_FULL,
                        "У защищающегося недостаточно карт для защиты ещё одной",
                    )

        # Убираем карту у игрока из руки, потому что атака прошла успешно
        attacker.remove_card(player_input.attack_card)

        return StateResponse(
            ActionResult.SUCCESS,
            f"Игрок {player_input.player_id} атакует картой {player_input.attack_card}.",
            None,
            {
                "attacker_id": self.game.current_attacker_id,
                "defender_id": self.game.current_defender_id,
                "attack_card": player_input.attack_card,
                "table_cards": self.game.game_table.table_cards,
            },
        )

    def _check_defend_rules(self, player_input: PlayerInput) -> StateResponse:
        # Проверка наличия карты для защиты
        if not player_input.defend_card:
            return StateResponse(
                ActionResult.CARD_REQUIRED, "Необходимо выбрать карту для защиты."
            )
        try:
            defender: Player = self.game.players[self.game.current_defender_idx]
        except (TypeError, IndexError):
            return StateResponse(
                ActionResult.INTERNAL_ERROR, "Не найден игрок для защиты"
            )
        # Проверяем, что карта есть у игрока
        defender = self.game.get_player_by_id(self.game.current_defender_id)
        if not defender or player_input.defend_card not in defender.get_cards():
            return StateResponse(ActionResult.INVALID_CARD, "У вас нет такой карты.")

        # Логика защиты (cover card)
        try:
            if not self.game.game_table.cover_card(
                player_input.attack_card, player_input.defend_card
            ):
                return StateResponse(
                    ActionResult.INVALID_CARD,
                    "Этой картой нельзя покрыть карту на столе",
                    None,
                    {
                        "attack_card": player_input.attack_card,
                        "defend_card": player_input.defend_card,
                    },
                )
        except ValueError:
            return StateResponse(
                ActionResult.INVALID_CARD,
                "Ошибка с картой на столе",
            )

        defender.remove_card(player_input.defend_card)

        return StateResponse(
            ActionResult.SUCCESS,
            f"Игрок {player_input.player_id} защищается картой {player_input.defend_card}.",
            None,
            {
                "defender_id": self.game.current_defender_id,
                "defend_card": player_input.defend_card,
                "table_cards": self.game.game_table.table_cards,
            },
        )

    def _is_defender_able_to_beat_more(
        self, defender_cards: list[Card]
    ) -> (
        bool
    ):  # TODO вообще здесь нужно добавить проверку на лимиты стола по идее. Я так понял нигде с ними то особо и не работаю
        """
        Проверяет, может ли защищающийся игрок отбить еще одну карту на столе

        Returns:
            bool: True, если может отбить ещё, иначе False
        """
        if len(self.game.game_table.table_cards) == 0:
            return True
        elif len(defender_cards) < len(
            [
                card["attack_card"]
                for card in self.game.game_table.table_cards
                if card["defend_card"] is None
            ]
        ):
            return False
        else:
            return True

    def _handle_player_quit_action(self, player_input: PlayerInput) -> StateResponse:
        if pl := self.game.get_player_by_id(player_input.player_id):
            pl.status = PlayerStatus.LEAVED

            return StateResponse(
                ActionResult.SUCCESS,
                f"Игрок {player_input.player_id} покинул игру. Игра завершена.",
                "GameOverState",
                {"players_count": len(self.game.players)},
            )
        else:
            return StateResponse(
                ActionResult.INVALID_ACTION,
                f"Игрок {player_input.player_id} не найден.",
            )

    def _is_all_cards_defended(self) -> bool:
        """
        Проверяет, все ли карты на столе отбиты

        Returns:
            bool: True, если все карты отбиты, иначе False
        """
        if not all(
            card.get("defend_card") for card in self.game.game_table.table_cards
        ):
            return False
        self.game.round_defender_status = PlayerAction.DEFEND
        return True

    def _are_all_cards_on_table_defended(self) -> bool:
        """Проверяет, все ли карты на столе отбиты, без побочных эффектов."""
        if not self.game.game_table.table_cards:
            return True
        return all(
            card.get("defend_card") for card in self.game.game_table.table_cards
        )

    def get_allowed_actions(self) -> Dict[str, List[str]]:
        """
        Возвращает список разрешенных действий для каждого игрока.
        Возвращает имена действий (строки), а не члены Enum.
        """
        # By default, players can only quit.
        allowed_actions = {p.id_: [PlayerAction.QUIT.name] for p in self.game.players}

        attacker_id = self.game.current_attacker_id
        defender_id = self.game.current_defender_id
        is_defender_collecting = self.game.round_defender_status == PlayerAction.COLLECT
        all_cards_beaten = self._are_all_cards_on_table_defended()

        # Determine Attacker's actions
        if attacker_id in allowed_actions:
            # Attacker can always try to attack. The validation is in handle_input.
            allowed_actions[attacker_id].append(PlayerAction.ATTACK.name)

            # Attacker can pass if the defender is taking cards, or if all cards are beaten.
            if is_defender_collecting or (self.game.game_table.table_cards and all_cards_beaten):
                allowed_actions[attacker_id].append(PlayerAction.PASS.name)

        # Determine Defender's actions
        if defender_id in allowed_actions and not is_defender_collecting and not all_cards_beaten:
            # The defender can only act if they haven't decided to take the cards
            # AND there are still cards to be beaten.
            allowed_actions[defender_id].extend([
                PlayerAction.DEFEND.name,
                PlayerAction.PASS.name
            ])

        return allowed_actions

    def get_state_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о текущем состоянии

        Returns:
            Dict[str, Any]: Информация о состоянии
        """
        return {
            "attacker_id": self.game.current_attacker_id,
            "defender_id": self.game.current_defender_id,
            "table_cards": self.game.game_table.table_cards,
        }

    class PlayRoundWithThrowState(GameState, ExtraThrowActionMixin):
        """
        Состояние игры с использованием дополнительного броска карты
        """

        def __init__(self, game: FoolGame):
            super().__init__(game)
