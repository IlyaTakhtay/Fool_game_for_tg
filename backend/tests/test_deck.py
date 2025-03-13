import pytest

from backend.app.models.card import Card, TrumpCard, Suit, Rank
from backend.app.models.deck import Deck


@pytest.fixture
def deck():
    """Создание экземпляра колоды для каждого теста"""
    return Deck()

def test_initialization(deck):
    """Тест инициализации колоды"""
    # Проверяем, что колода содержит карты
    assert len(deck) == 36  # 36 карт в стандартной колоде
    # Проверяем, что козырная масть и карта установлены
    assert deck.trump_suit is not None
    assert deck.trump_card is not None
    # Проверяем, что trump_suit возвращает значение типа Suit
    assert isinstance(deck.trump_suit, Suit)
    # Проверяем, что козырная карта является объектом TrumpCard
    assert isinstance(deck.trump_card, TrumpCard)
    # Проверяем, что козырная карта последняя в колоде
    assert deck._cards[0] == deck.trump_card

def test_shuffle(deck):
    """Тест перемешивания колоды"""
    # Сохраняем копию карт до перемешивания
    cards_before = deck._cards.copy()
    # Перемешиваем колоду
    deck.shuffle()
    # Проверяем, что количество карт не изменилось
    assert len(deck) == len(cards_before)
    # Проверяем, что все карты сохранились (хотя порядок мог измениться)
    assert {(card.rank, card.suit) for card in deck._cards} == {(card.rank, card.suit) for card in cards_before}

def test_draw(deck):
    """Тест взятия карты из колоды"""
    initial_size = len(deck)
    
    # Берем карту из колоды
    card = deck.draw()
    
    # Проверяем, что карта не None
    assert card is not None
    # Проверяем, что размер колоды уменьшился
    assert len(deck) == initial_size - 1

def test_draw_until_empty(deck):
    """Тест взятия всех карт из колоды до опустошения"""
    # Берем все карты из колоды
    cards = []
    while len(deck) > 0:
        card = deck.draw()
        cards.append(card)
    
    # Проверяем, что колода пуста
    assert len(deck) == 0
    # Проверяем, что draw из пустой колоды возвращает None
    assert deck.draw() is None
    # Проверяем, что мы получили ожидаемое количество карт
    assert len(cards) == 36

def test_cards_uniqueness_and_completeness(deck):
    """Тест уникальности и полноты карт в колоде"""
    # Собираем все карты из колоды
    cards = []
    while len(deck) > 0:
        cards.append(deck.draw())
    
    # Получаем козырную масть
    trump_suit = next((card.suit for card in cards if isinstance(card, TrumpCard)), None)
    
    # Проверяем, что колода содержит все комбинации ранг-масть и карты правильного типа
    for rank in Rank:
        for suit in Suit:
            # Ищем карту с данным рангом и мастью
            matching_cards = [card for card in cards if card.rank == rank and card.suit == suit]
            # Проверяем, что такая карта ровно одна
            assert len(matching_cards) == 1, f"Ожидалась ровно одна карта для {rank} {suit}"
            
            # Проверяем тип карты в зависимости от масти
            if suit == trump_suit:
                assert isinstance(matching_cards[0], TrumpCard), f"Карта {matching_cards[0]} должна быть TrumpCard"
            else:
                assert not isinstance(matching_cards[0], TrumpCard), f"Карта {matching_cards[0]} не должна быть TrumpCard"
