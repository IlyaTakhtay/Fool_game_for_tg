import uuid
import pytest
from backend.app.models.deck import Deck
from backend.app.states.deal_state import DealState
from backend.app.models.game import FoolGame
from backend.app.models.player import Player, PlayerStatus
from backend.app.models.card import Card, Suit, Rank
from backend.app.contracts.game_contract import PlayerInput, PlayerAction, StateResponse, ActionResult

@pytest.fixture
def game_with_players():
    players = [Player(id_=1, name="Player1"), Player(id_=2, name="Player2"), Player(id_=3, name="Player3")]
    game = FoolGame(game_id=str(uuid.uuid4()), players_limit=3)
    game.players.extend(players)
    game.deck = Deck()
    game.deck.generate_deck()
    game.current_attacker_id = 1
    game.current_defender_id = 2
    return game

def test_enter(game_with_players):
    state = DealState(game_with_players)
    state.enter()
    
    # Проверка раздачи карт
    for player in game_with_players.players:
        assert len(player.get_cards()) == 6
    
    # Проверка сброса статусов
    for player in game_with_players.players:
        assert player.status == PlayerStatus.NOT_READY

def test_handle_input_continue(game_with_players):
    state = DealState(game_with_players)
    game_with_players.state_history = ["SomeState"]
    
    response = state.handle_input(PlayerInput(1, PlayerAction.ATTACK))
    assert response.result == ActionResult.SUCCESS
    assert "Продолжаем игру" in response.message

def test_handle_input_game_over(game_with_players):
    state = DealState(game_with_players)
    game_with_players.deck = []
    for p in game_with_players.players:
        p.cards = []
    
    response = state.handle_input(PlayerInput(1, PlayerAction.ATTACK))
    assert response.result == ActionResult.GAME_OVER

def test_exit(game_with_players):
    state = DealState(game_with_players)
    state.exit()
    assert game_with_players.current_attacker_id is not None
    assert game_with_players.current_defender_id is not None

def test_check_win_condition_all_victory(game_with_players):
    state = DealState(game_with_players)
    game_with_players.deck = []
    for p in game_with_players.players:
        p.cards = []
    
    assert state._check_win_condition() is True

def test_check_win_condition_one_active(game_with_players):
    state = DealState(game_with_players)
    game_with_players.deck = []
    game_with_players.players[0].cards = [Card(Suit.HEARTS, Rank.SIX)]
    
    assert state._check_win_condition() is True

def test_update_roles_after_defense(game_with_players):
    state = DealState(game_with_players)
    game_with_players.round_defender_status = PlayerAction.DEFEND
    game_with_players.current_defender_id = 2
    
    state._update_roles()
    assert game_with_players.current_attacker_id == 2
    assert game_with_players.current_defender_id == 3

def test_deal_cards_order(game_with_players):
    state = DealState(game_with_players)
    game_with_players.current_attacker_id = 3
    game_with_players.current_defender_id = 1
    # Проверяем порядок: атакующий (1), другие (2), защитник (0)
    for _ in range(30):
        state.game.deck.draw()
    state._deal_cards()
    assert len(game_with_players.players[2].get_cards()) == 6
    assert len(game_with_players.players[1].get_cards()) == 0
    assert len(game_with_players.players[0].get_cards()) == 0

    state.game.deck.generate_deck()
    for _ in range(30):
        state.game.deck.draw()
    state._deal_cards()
    
    assert len(game_with_players.players[2].get_cards()) == 6
    assert len(game_with_players.players[1].get_cards()) == 6
    assert len(game_with_players.players[0].get_cards()) == 0
    
    state.game.deck.generate_deck()
    for _ in range(30):
        state.game.deck.draw()
    state._deal_cards()
    
    assert len(game_with_players.players[2].get_cards()) == 6
    assert len(game_with_players.players[1].get_cards()) == 6
    assert len(game_with_players.players[0].get_cards()) == 6

def test_fill_hand_partial_deck(game_with_players):
    state = DealState(game_with_players)
    player = Player(id_=4, name="Sex")
    cards = [
        Card(Suit.HEARTS, Rank.SIX),
        Card(Suit.DIAMONDS, Rank.SEVEN),
        Card(Suit.CLUBS, Rank.EIGHT),
        Card(Suit.SPADES, Rank.NINE)
    ]
    for c in cards:
        player.add_card(c)
    for _ in range(34):
        game_with_players.deck.draw()
    state._fill_hand(player)
    assert len(player.get_cards()) == 6  # 4 + 2 = 6

def test_update_player_statuses(game_with_players):
    game_with_players.players[0].status = PlayerStatus.READY
    game_with_players.players[1].status = PlayerStatus.VICTORY
    
    state = DealState(game_with_players)
    state.update_player_statuses()
    
    assert game_with_players.players[0].status == PlayerStatus.NOT_READY
    assert game_with_players.players[1].status == PlayerStatus.VICTORY
