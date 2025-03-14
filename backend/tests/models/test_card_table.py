import pytest

from typing import List, Dict

from backend.app.models.card import Card, TrumpCard, Rank, Suit
from backend.app.models.card_table import CardTable

@pytest.fixture
def card_setup():
    """Создание тестовых карт для использования в тестах"""
    # Создаем тестовые карты
    six_hearts = Card(Rank.SIX, Suit.HEARTS)
    seven_hearts = Card(Rank.SEVEN, Suit.HEARTS)
    eight_hearts = Card(Rank.EIGHT, Suit.HEARTS)
    six_diamonds = Card(Rank.SIX, Suit.DIAMONDS)
    seven_diamonds = Card(Rank.SEVEN, Suit.DIAMONDS)
    eight_spades = Card(Rank.EIGHT, Suit.SPADES)
    nine_clubs = Card(Rank.NINE, Suit.CLUBS)
    ten_clubs = Card(Rank.TEN, Suit.CLUBS)
    six_spades = Card(Rank.SIX, Suit.SPADES)

    # Добавляем козырные карты
    trump_ace_diamonds = TrumpCard(Rank.ACE, Suit.DIAMONDS)
    trump_king_diamonds = TrumpCard(Rank.KING, Suit.DIAMONDS)
    trump_six_hearts = TrumpCard(Rank.SIX, Suit.HEARTS)
    
    # Добавляем обычные карты, аналогичные козырным
    ace_diamonds = Card(Rank.ACE, Suit.DIAMONDS)
    king_diamonds = Card(Rank.KING, Suit.DIAMONDS)
    
    return {
        "six_hearts": six_hearts,
        "seven_hearts": seven_hearts,
        "eight_hearts": eight_hearts,
        "six_diamonds": six_diamonds,
        "six_spades": six_spades,
        "seven_diamonds": seven_diamonds,
        "eight_spades": eight_spades,
        "nine_clubs": nine_clubs,
        "ten_clubs": ten_clubs,
        "trump_ace_diamonds": trump_ace_diamonds,
        "trump_king_diamonds": trump_king_diamonds,
        "trump_six_hearts": trump_six_hearts,
        "ace_diamonds": ace_diamonds,
        "king_diamonds": king_diamonds
    }


@pytest.fixture
def table():
    """Создание экземпляра стола для каждого теста"""
    return CardTable()

def test_initialization(table: CardTable):
    """Тест инициализации стола"""
    assert table.slots == 5
    assert len(table.table_cards) == 0

def test_throw_first_card(table: CardTable, card_setup: Dict[str, Card]):
    """Тест добавления первой карты на стол"""
    result = table.throw_card(card_setup["six_hearts"])
    if not isinstance(result, Exception) and result.get("status"):
        assert result["status"] is "success"

    assert len(table.table_cards) == 1
    assert table.table_cards[0]['attack_card'] == card_setup["six_hearts"]

def test_throw_matching_rank_card(table: CardTable, card_setup: Dict[str, Card]):
    """Тест добавления карты с совпадающим рангом"""
    table.throw_card(card_setup["six_hearts"])
    result = table.throw_card(card_setup["six_diamonds"])
    if not isinstance(result, Exception) and result.get("status"):
        assert result["status"] is "success"
    assert len(table.table_cards) == 2
    assert table.table_cards[1]['attack_card'] == card_setup["six_diamonds"]

def test_throw_non_matching_rank_card(table: CardTable, card_setup: Dict[str, Card]):
    """Тест добавления карты с несовпадающим рангом"""
    table.throw_card(card_setup["six_hearts"])
    result = table.throw_card(card_setup["seven_diamonds"])
    if not isinstance(result, Exception) and result.get("status"):
        assert result["status"] is "error"
    assert len(table.table_cards) == 1

def test_throw_card_exceed_slots(table: CardTable, card_setup: Dict[str, Card]):
    """Тест добавления карты при превышении количества слотов"""
    table.slots = 2
    table.throw_card(card_setup["six_hearts"])
    table.throw_card(card_setup["six_diamonds"])
    result = table.throw_card(card_setup["six_spades"])  # Пытаемся добавить третью карту
    assert result is False
    assert len(table.table_cards) == 2

def test_cover_card_success(table: CardTable, card_setup: Dict[str, Card]):
    """Тест успешного покрытия карты"""
    table.throw_card(card_setup["six_hearts"])
    result = table.cover_card(card_setup["six_hearts"], card_setup["seven_hearts"])
    assert result is True
    assert table.table_cards[0]['defend_card'] == card_setup["seven_hearts"]

def test_cover_card_failure_lower_rank(table: CardTable, card_setup: Dict[str, Card]): 
    """Тест неудачного покрытия карты из-за более низкого ранга"""
    table.throw_card(card_setup["seven_hearts"])
    result = table.cover_card(card_setup["seven_hearts"], card_setup["six_hearts"])
    assert result is False
    assert table.table_cards[0].get('defend_card') is None

def test_cover_card_not_on_table(table: CardTable, card_setup: Dict[str, Card]):
    """Тест покрытия карты, которой нет на столе"""
    with pytest.raises(ValueError):
        table.cover_card(card_setup["six_hearts"], card_setup["seven_hearts"])

def test_get_attack_cards(table: CardTable, card_setup: Dict[str, Card]):
    """Тест получения атакующих карт"""
    table.throw_card(card_setup["six_hearts"])
    table.throw_card(card_setup["six_diamonds"])
    attack_cards = table._get_attack_cards()
    assert len(attack_cards) == 2
    assert card_setup["six_hearts"] in attack_cards
    assert card_setup["six_diamonds"] in attack_cards

def test_get_defend_cards(table: CardTable, card_setup: Dict[str, Card]):
    """Тест получения защищающих карт"""
    table.throw_card(card_setup["six_hearts"])
    table.throw_card(card_setup["six_diamonds"])
    table.cover_card(card_setup["six_hearts"], card_setup["seven_hearts"])
    defend_cards = table._get_defend_cards()
    assert len(defend_cards) == 1
    assert card_setup["seven_hearts"] in defend_cards

def test_get_card_index(table: CardTable, card_setup: Dict[str, Card]):
    """Тест получения индекса карты"""
    table.throw_card(card_setup["six_hearts"])
    table.throw_card(card_setup["six_diamonds"])
    table.cover_card(card_setup["six_hearts"], card_setup["seven_hearts"])
    idx_attack = table._get_card_index(card_setup["six_hearts"])
    idx_defend = table._get_card_index(card_setup["seven_hearts"])
    assert idx_attack == 0
    assert idx_defend == 0
    idx_not_found = table._get_card_index(card_setup["eight_spades"])
    assert idx_not_found is None

def test_clear_table(table: CardTable, card_setup: Dict[str, Card]):
    """Тест очистки стола"""
    table.throw_card(card_setup["six_hearts"])
    table.throw_card(card_setup["six_diamonds"])
    table.clear_table()
    assert len(table.table_cards) == 0
    assert len(table._get_attack_cards()) == 0
    assert len(table._get_defend_cards()) == 0

def test_throw_trump_card(table: CardTable, card_setup: Dict[str, Card]):
    """Тест добавления козырной карты на стол"""
    result = table.throw_card(card_setup["trump_ace_diamonds"])
    assert result is True
    assert len(table.table_cards) == 1
    assert table.table_cards[0]['attack_card'] == card_setup["trump_ace_diamonds"]

def test_cover_card_with_trump(table: CardTable, card_setup: Dict[str, Card]):
    """Тест покрытия обычной карты козырной картой"""
    table.throw_card(card_setup["ace_diamonds"])
    result = table.cover_card(card_setup["ace_diamonds"], card_setup["trump_six_hearts"])
    assert result is True
    assert table.table_cards[0]['defend_card'] == card_setup["trump_six_hearts"]

def test_cover_trump_with_higher_trump(table: CardTable, card_setup: Dict[str, Card]):
    """Тест покрытия козырной карты другой козырной картой более высокого ранга"""
    table.throw_card(card_setup["trump_six_hearts"])
    result = table.cover_card(card_setup["trump_six_hearts"], card_setup["trump_king_diamonds"])
    assert result is True
    assert table.table_cards[0]['defend_card'] == card_setup["trump_king_diamonds"]

def test_cover_trump_with_regular_card_failure(table: CardTable, card_setup: Dict[str, Card]):
    """Тест неудачного покрытия козырной карты обычной картой"""
    table.throw_card(card_setup["trump_six_hearts"])
    result = table.cover_card(card_setup["trump_six_hearts"], card_setup["ace_diamonds"])
    assert result is False
    assert table.table_cards[0].get('defend_card') is None

def test_trump_card_index(table: CardTable, card_setup: Dict[str, Card]):
    """Тест получения индекса козырной карты"""
    table.throw_card(card_setup["trump_ace_diamonds"])
    idx = table._get_card_index(card_setup["trump_ace_diamonds"])
    assert idx == 0

def test_add_trump_card_and_no_trump_copy(table: CardTable, card_setup: Dict[str, Card]):
    """Тест добавления козырной карты и попытка добавления её не-козырной копии"""
    # Добавляем козырного туза
    table.throw_card(card_setup["trump_ace_diamonds"])
    assert len(table.table_cards) == 1
    
    # Добавляем обычного туза той же масти
    with pytest.raises(ValueError):
        result = table.throw_card(card_setup["ace_diamonds"])
    
    # Проверяем, что вторая карта не добавилась
    attack_cards = table._get_attack_cards()
    assert len(table.table_cards) == 1
    assert len(attack_cards) == 1
    assert card_setup["trump_ace_diamonds"] in attack_cards

def test_cover_multiple_cards_with_trump(table: CardTable, card_setup: Dict[str, Card]):
    """Тест покрытия нескольких карт, включая козырные"""
    # Добавляем несколько карт на стол
    table.throw_card(card_setup["six_hearts"])
    table.throw_card(card_setup["six_diamonds"])
    table.throw_card(card_setup["trump_ace_diamonds"])

    assert len(table.table_cards) == 2

    # Покрываем одну обычную и одну козырную
    table.cover_card(card_setup["six_hearts"], card_setup["seven_hearts"])
    table.cover_card(card_setup["six_diamonds"], card_setup["trump_ace_diamonds"])
    
    # Проверяем результат
    defend_cards = table._get_defend_cards()
    assert len(defend_cards) == 2
    assert card_setup["seven_hearts"] in defend_cards
    assert card_setup["trump_ace_diamonds"] in defend_cards

def test_clear_table_with_trump_cards(table: CardTable, card_setup: Dict[str, Card]):
    """Тест очистки стола с козырными картами"""
    table.throw_card(card_setup["six_hearts"])
    table.throw_card(card_setup["trump_ace_diamonds"])
    table.cover_card(card_setup["six_hearts"], card_setup["trump_six_hearts"])
    
    table.clear_table()
    assert len(table.table_cards) == 0
    assert len(table._get_attack_cards()) == 0
    assert len(table._get_defend_cards()) == 0
