# попросить написать чатгпт тесты сюда и на этом все на сегодняшний день
import random
import pytest
from unittest.mock import Mock, patch, MagicMock

from backend.app.contracts.game_contract import PlayerInput, PlayerAction, ActionResult, StateResponse
from backend.app.models.player import Player, PlayerStatus
from backend.app.models.card import Card, Suit, Rank
from backend.app.states.play_round_state import PlayRoundState

@pytest.fixture
def game_mock():
    """Фикстура игры с MagicMock для поддержки магических методов"""
    game = MagicMock()

    # Создаем реалистичных игроков
    player1 = MagicMock(spec=Player)  # Добавляем spec для валидации методов
    player1.id = "1"
    player1.cards = {
        Card(Suit.HEARTS, Rank.ACE),
        Card(Suit.DIAMONDS, Rank.KING)
    }
    player1.get_cards.return_value = player1.cards  # Явный возврат множества
    player1.remove_card = MagicMock()  # Явно инициализируем метод

    player2 = MagicMock(spec=Player)
    player2.id = "2"
    player2.cards = {
        Card(Suit.CLUBS, Rank.QUEEN),
        Card(Suit.SPADES, Rank.JACK)
    }
    player2.get_cards.return_value = player2.cards
    player2.remove_card = MagicMock()

    # Настраиваем игровой стол
    game_table = MagicMock()
    game_table.table_cards = []  # Реальный список, а не Mock
    game_table.throw_card.return_value = {"status": "success"}

    # Собираем объект игры
    game.players = [player1, player2]
    game.current_attacker_id = "1"
    game.current_defender_id = "2"
    game.game_table = game_table
    game.deck = MagicMock()

    return game



@pytest.fixture
def fight_state(game_mock):
    """Фикстура для создания состояния боя"""
    return PlayRoundState(game_mock)


def test_enter(fight_state, game_mock):
    """Тест входа в состояние боя"""
    result = fight_state.enter()
    
    game_mock.game_table.clear_table.assert_called_once()
    assert "message" in result
    assert result["attacker_id"] == "1"
    assert result["defender_id"] == "2"
    assert result["table_cards"] == []


def test_exit(fight_state, game_mock):
    """Тест выхода из состояния боя"""
    game_mock.game_table.table_cards = [Card(Suit.HEARTS, Rank.ACE)]
    
    result = fight_state.exit()
    
    assert "message" in result
    assert "table_cards" in result


def test_handle_input_quit(fight_state, game_mock):
    """Тест обработки выхода игрока"""
    player_input = PlayerInput(player_id="1", action=PlayerAction.QUIT)
    
    response = fight_state.handle_input(player_input)
    
    assert response.result == ActionResult.SUCCESS
    assert response.next_state == "LobbyState"
    assert "покинул игру" in response.message


def test_handle_input_not_your_turn(fight_state, game_mock):
    """Тест обработки хода не в свою очередь"""
    player_input = PlayerInput(player_id="3", action=PlayerAction.ATTACK)
    
    response = fight_state.handle_input(player_input)
    
    assert response.result == ActionResult.NOT_YOUR_TURN


def test_handle_input_attack_no_card(fight_state, game_mock):
    """Тест атаки без указания карты"""
    player_input = PlayerInput(player_id="1", action=PlayerAction.ATTACK)
    
    response = fight_state.handle_input(player_input)
    
    assert response.result == ActionResult.CARD_REQUIRED


def test_handle_input_attack_invalid_card(fight_state, game_mock):
    """Тест атаки с недопустимой картой"""
    invalid_card = Card(Suit.CLUBS, Rank.TEN)
    player_input = PlayerInput(player_id="1", action=PlayerAction.ATTACK, attack_card=invalid_card)
    
    response = fight_state.handle_input(player_input)
    
    assert response.result == ActionResult.INVALID_CARD


def test_handle_input_attack_success(fight_state, game_mock):
    """Тест успешной атаки"""
    attack_card = Card(Suit.HEARTS, Rank.ACE)
    player_input = PlayerInput(player_id="1", action=PlayerAction.ATTACK, attack_card=attack_card)
    
    game_mock.game_table.throw_card.return_value = {"status": "success", "message": "success"}
    
    response = fight_state.handle_input(player_input)
    
    assert response.result == ActionResult.SUCCESS
    assert "атакует картой" in response.message
    game_mock.players[0].remove_card.assert_called_once_with(attack_card)


def test_handle_input_attack_table_full_by_table_limit(fight_state, game_mock):
    """Тест атаки при полном """
    attack_card = Card(Suit.HEARTS, Rank.ACE)
    player_input = PlayerInput(player_id="1", action=PlayerAction.ATTACK, attack_card=attack_card)
    
    game_mock.game_table.slots = 6
    game_mock.game_table.table_cards = [{"attack_card":Card(random.choice(list(Suit)), random.choice(list(Rank)))} for _ in range(2)]
    
    response = fight_state.handle_input(player_input)
    
    assert response.result == ActionResult.TABLE_FULL

def test_handle_input_attack_table_full_by_player_hand(fight_state, game_mock):
    """Тест атаки при полном """
    attack_card = Card(Suit.HEARTS, Rank.ACE)
    player_input = PlayerInput(player_id="1", action=PlayerAction.ATTACK, attack_card=attack_card)
    
    game_mock.game_table.table_cards = game_mock.game_table.table_cards = [
        {"attack_card": Card(Suit.DIAMONDS, Rank.KING)}
    ]
    game_mock.game_table.slots = 1
    
    game_mock.game_table.throw_card.return_value = {
        "status": "failed", 
        "message": "no free slots"
    }
    response = fight_state.handle_input(player_input)
    
    game_mock.game_table.throw_card.assert_called_once_with(attack_card)

    assert response.result == ActionResult.TABLE_FULL

def test_handle_input_attack_wrong_rank(fight_state, game_mock):
    """Тест атаки с неправильным рангом"""
    attack_card = Card(Suit.HEARTS, Rank.ACE)
    player_input = PlayerInput(player_id="1", action=PlayerAction.ATTACK, attack_card=attack_card)
    
    game_mock.game_table.throw_card.return_value = {"status": "failed", "message": "wrong rank"}
    game_mock.game_table.table_cards = [Card(Suit.CLUBS, Rank.KING)]
    
    response = fight_state.handle_input(player_input)
    
    assert response.result == ActionResult.WRONG_CARD


def test_handle_input_attack_defender_has_few_cards(fight_state, game_mock):
    """Тест атаки, когда у защищающегося мало карт"""
    attack_card = Card(Suit.HEARTS, Rank.ACE)
    player_input = PlayerInput(player_id="1", action=PlayerAction.ATTACK, attack_card=attack_card)
    
    game_mock.game_table.throw_card.return_value = {"status": "success", "message": "success"}
    game_mock.game_table.table_cards = [Card(Suit.CLUBS, Rank.KING), Card(Suit.DIAMONDS, Rank.QUEEN)]
    game_mock.players[1].cards = [Card(Suit.CLUBS, Rank.QUEEN), Card(Suit.SPADES, Rank.JACK)]
    
    response = fight_state.handle_input(player_input)
    
    assert response.result == ActionResult.TABLE_FULL
    assert "недостаточно карт" in response.message


def test_handle_input_defend_no_card(fight_state, game_mock):
    """Тест защиты без указания карты"""
    player_input = PlayerInput(player_id="2", action=PlayerAction.DEFEND)
    
    response = fight_state.handle_input(player_input)
    
    assert response.result == ActionResult.CARD_REQUIRED


def test_handle_input_defend_invalid_card(fight_state, game_mock):
    """Тест защиты с недопустимой картой"""
    invalid_card = Card(Suit.CLUBS, Rank.TEN)
    player_input = PlayerInput(player_id="2", action=PlayerAction.DEFEND, defend_card=invalid_card)
    
    response = fight_state.handle_input(player_input)
    
    assert response.result == ActionResult.INVALID_CARD


def test_handle_input_defend_cannot_beat(fight_state, game_mock):
    """Тест защиты, когда карта не может побить атакующую"""
    attack_card = Card(Suit.HEARTS, Rank.ACE)
    defend_card = Card(Suit.CLUBS, Rank.QUEEN)
    player_input = PlayerInput(
        player_id="2", 
        action=PlayerAction.DEFEND, 
        attack_card=attack_card,
        defend_card=defend_card
    )
    
    game_mock.game_table.cover_card.return_value = False
    
    response = fight_state.handle_input(player_input)
    
    assert response.result == ActionResult.INVALID_CARD
    assert "нельзя покрыть" in response.message


def test_handle_input_defend_success(fight_state, game_mock):
    """Тест успешной защиты"""
    attack_card = Card(Suit.HEARTS, Rank.ACE)
    defend_card = Card(Suit.CLUBS, Rank.QUEEN)
    player_input = PlayerInput(
        player_id="2", 
        action=PlayerAction.DEFEND, 
        attack_card=attack_card,
        defend_card=defend_card
    )
    
    game_mock.game_table.cover_card.return_value = True
    
    response = fight_state.handle_input(player_input)
    
    assert response.result == ActionResult.SUCCESS
    assert "защищается картой" in response.message


def test_handle_input_pass_cards_not_defended(fight_state, game_mock):
    """Тест паса, когда не все карты отбиты"""
    player_input = PlayerInput(player_id="1", action=PlayerAction.PASS)
    
    with patch.object(fight_state, '_all_cards_defended', return_value=False):
        response = fight_state.handle_input(player_input)
    
    assert response.result == ActionResult.INVALID_ACTION
    assert "Нельзя пасовать" in response.message


def test_handle_input_pass_success(fight_state, game_mock):
    """Тест успешного паса"""
    player_input = PlayerInput(player_id="1", action=PlayerAction.PASS)
    
    with patch.object(fight_state, '_all_cards_defended', return_value=True):
        with patch.object(fight_state, 'update_after_successful_defense', return_value={}):
            response = fight_state.handle_input(player_input)
    
    assert response.result == ActionResult.SUCCESS
    assert "успешно отбился" in response.message


def test_handle_input_collect(fight_state, game_mock):
    """Тест сбора карт защищающимся"""
    player_input = PlayerInput(player_id="2", action=PlayerAction.COLLECT)
    
    response = fight_state.handle_input(player_input)
    
    assert response.result == ActionResult.SUCCESS
    assert response.next_state == "OnlyThrowState"


def test_handle_input_invalid_action(fight_state, game_mock):
    """Тест недопустимого действия"""
    player_input = PlayerInput(player_id="1", action=PlayerAction.READY)
    
    response = fight_state.handle_input(player_input)
    
    assert response.result == ActionResult.INVALID_ACTION


def test_update_after_successful_defense(fight_state, game_mock):
    """Тест обновления после успешной защиты"""
    with patch.object(fight_state, '_deal_cards'):
        result = fight_state.update_after_successful_defense()
    
    game_mock.game_table.clear_table.assert_called()
    assert "message" in result
    assert "attacker_id" in result
    assert "defender_id" in result


def test_all_cards_defended_true(fight_state, game_mock):
    """Тест проверки, что все карты отбиты (положительный)"""
    game_mock.game_table.table_cards = [
        {"attack_card": Card(Suit.HEARTS, Rank.ACE), "defend_card": Card(Suit.SPADES, Rank.ACE)},
        {"attack_card": Card(Suit.DIAMONDS, Rank.KING), "defend_card": Card(Suit.SPADES, Rank.ACE)}
    ]
    
    result = fight_state._all_cards_defended()
    
    assert result is True


def test_all_cards_defended_false(fight_state, game_mock):
    """Тест проверки, что все карты отбиты (отрицательный)"""
    game_mock.game_table.table_cards = [
        {"attack_card": Card(Suit.HEARTS, Rank.ACE), "defend_card": Card(Suit.SPADES, Rank.ACE)},
        {"attack_card": Card(Suit.DIAMONDS, Rank.KING)}
    ]
    
    result = fight_state._all_cards_defended()
    
    assert result is False


def test_deal_cards(fight_state, game_mock):
    """Тест раздачи карт"""
    # Настраиваем моки
    game_mock.deck.draw.side_effect = [
        Card(Suit.HEARTS, Rank.TEN),
        Card(Suit.DIAMONDS, Rank.NINE),
        Card(Suit.CLUBS, Rank.EIGHT),
        Card(Suit.SPADES, Rank.SEVEN),
        None  # Колода закончилась
    ]
    
    # Вызываем тестируемый метод
    fight_state._deal_cards()
    
    # Проверяем, что карты были добавлены игрокам
    assert game_mock.deck.draw.call_count > 0
    assert game_mock.players[0].add_card.call_count > 0


def test_get_allowed_actions(fight_state, game_mock):
    """Тест получения разрешенных действий"""
    # Добавляем третьего игрока
    game_mock.players.append(Mock(id="3", cards=[]))
    
    allowed_actions = fight_state.get_allowed_actions()
    
    assert "1" in allowed_actions
    assert "2" in allowed_actions
    assert "3" in allowed_actions
    assert PlayerAction.ATTACK in allowed_actions["1"]
    assert PlayerAction.PASS in allowed_actions["1"]
    assert PlayerAction.DEFEND in allowed_actions["2"]
    assert PlayerAction.COLLECT in allowed_actions["2"]
    assert [PlayerAction.QUIT] == allowed_actions["3"]


def test_get_state_info(fight_state, game_mock):
    """Тест получения информации о состоянии"""
    game_mock.game_table.table_cards = [Card(Suit.HEARTS, Rank.ACE)]
    
    state_info = fight_state.get_state_info()
    
    assert state_info["attacker_id"] == "1"
    assert state_info["defender_id"] == "2"
    assert len(state_info["table_cards"]) == 1
