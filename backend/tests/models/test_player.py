import pytest
import uuid

from backend.app.models.card import Card, TrumpCard, Rank, Suit
from backend.app.models.player import Player


@pytest.fixture
def card_setup():
    """Создание тестовых карт для использования в тестах"""
    # Создаем тестовые карты
    six_hearts = Card(Rank.SIX, Suit.HEARTS)
    seven_hearts = Card(Rank.SEVEN, Suit.HEARTS)
    queen_spades = Card(Rank.QUEEN, Suit.SPADES)
    trump_ten = TrumpCard(Rank.TEN, Suit.CLUBS)
    trump_ace = TrumpCard(Rank.ACE, Suit.DIAMONDS)
    ace_diamonds = TrumpCard(Rank.ACE, Suit.DIAMONDS)

    
    return {
        "six_hearts": six_hearts,
        "seven_hearts": seven_hearts,
        "queen_spades": queen_spades,
        "trump_ten": trump_ten,
        "trump_ace": trump_ace,
        "ace_diamonds": ace_diamonds
    }

@pytest.fixture
def player():
    """Создание экземпляра игрока для каждого теста"""
    return Player(name="George", id_=str(uuid.uuid4().int))

def test_initialization():
    """Тест инициализации игрока"""
    player_id = str(uuid.uuid4())
    player = Player(name="George", id_=player_id)
    assert player.name == "George"
    assert player.id_ == player_id
    assert len(player._hand) == 0

# def test_initialization_empty_name():
#     """Тест создания игрока с пустым именем"""
#     with pytest.raises(ValueError):
#         Player(name="", id_=uuid.uuid4().hex)

# def test_initialization_empty_id():
#     """Тест создания игрока с пустым ID"""
#     with pytest.raises(ValueError):
#         Player(name="George", id_="")

def test_add_card_to_player(player: Player, card_setup):
    """Тест добавления карты игроку"""
    card = card_setup["six_hearts"]
    result = player.add_card(card=card)
    assert result is None
    assert len(player._hand) == 1
    assert card in player._hand

def test_add_duplicate_card(player: Player, card_setup):
    """Тест добавления дублирующейся карты"""
    card = card_setup["six_hearts"]
    player.add_card(card=card)
    with pytest.raises(ValueError):
        player.add_card(card=card)
    assert len(player._hand) == 1

def test_add_trump_card_and_no_trump_copy(player: Player, card_setup):
    """Тест добавления козырной карты"""
    card = card_setup["trump_ace"]
    result = player.add_card(card=card)
    assert result is None
    assert len(player._hand) == 1
    assert card in player._hand
    no_trump_copy = card_setup["ace_diamonds"]
    with pytest.raises(ValueError):
        result = player.add_card(card=no_trump_copy)
    assert len(player._hand) == 1
    assert card in player._hand
    

def test_add_mixed_cards(player: Player, card_setup):
    """Тест добавления нескольких разных карт"""
    player.add_card(card=card_setup["six_hearts"])
    player.add_card(card=card_setup["queen_spades"])
    player.add_card(card=card_setup["trump_ace"])
    assert len(player._hand) == 3

def test_remove_card_success(player: Player, card_setup):
    """Тест успешного удаления карты из руки игрока"""
    card = card_setup["six_hearts"]
    player.add_card(card)
    result = player.remove_card(card)
    assert result is None
    assert len(player._hand) == 0
    assert card not in player._hand

def test_remove_trump_card(player: Player, card_setup):
    """Тест удаления козырной карты из руки игрока"""
    card = card_setup["trump_ten"]
    player.add_card(card)
    result = player.remove_card(card)
    assert result is None
    assert len(player._hand) == 0
    assert card not in player._hand

def test_remove_nonexistent_card(player: Player, card_setup):
    """Тест удаления карты, которой нет в руке игрока"""
    # Руку игрока наполняем некоторыми картами
    player.add_card(card_setup["six_hearts"])
    player.add_card(card_setup["queen_spades"])
    
    # Пытаемся удалить карту, которой нет в руке
    with pytest.raises(ValueError):
        player.remove_card(card_setup["seven_hearts"])
    
    # Убеждаемся, что рука не изменилась
    assert len(player._hand) == 2

def test_get_cards(player: Player, card_setup):
    """Тест получения всех карт из руки игрока"""
    player.add_card(card_setup["six_hearts"])
    player.add_card(card_setup["queen_spades"])
    cards = player.get_cards()
    assert len(cards) == 2
    assert card_setup["six_hearts"] in cards
    assert card_setup["queen_spades"] in cards

def test_clear_hand(player: Player, card_setup):
    """Тест очистки руки игрока"""
    player.add_card(card_setup["six_hearts"])
    player.add_card(card_setup["queen_spades"])
    player.clear_hand()
    assert len(player._hand) == 0
