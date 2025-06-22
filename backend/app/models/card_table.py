from typing import List, Dict, Set

from backend.app.models.card import Card, TrumpCard, Rank
from backend.app.utils.errors import (
    InvalidDefenseError,
    WeakDefenseError,
    CardNotOnTableError,
    InvalidThrowError,
    CardAlreadyOnTableError,
    NoFreeSlotsError,
)

class CardTable:
    def __init__(self) -> None:
        self.slots = 5
        self.table_cards: List[Dict] = [] #TODO: make table_cards only getter without setter

    def _get_attack_cards(self) -> List[Card]:
        attack_cards = []
        for pack in self.table_cards:
            card = pack.get('attack_card')
            if card is not None:
                attack_cards.append(pack['attack_card'])
        return attack_cards

    def _get_defend_cards(self) -> List[Card]:
        defend_cards = []
        for pack in self.table_cards:
            card = pack.get('defend_card')
            if card is not None:
                defend_cards.append(card)
        return defend_cards
    
    def _get_card_index(self, to_search_card: Card) -> int | None:
        for i, pack in enumerate(self.table_cards):
            attack = pack.get('attack_card')
            defend = pack.get('defend_card')
            if attack == to_search_card:
                return i
            elif defend == to_search_card:
                return i
        return None

    def _get_table_ranks(self) -> Set[Rank]:
        """Возвращает множество рангов карт на столе"""
        ranks = set()
        for pack in self.table_cards:
            attack_card = pack.get('attack_card')
            defend_card = pack.get('defend_card')
            if attack_card:
                ranks.add(attack_card.rank)
            if defend_card:
                ranks.add(defend_card.rank)
        return ranks

    def clear_table(self) -> None:
        self.table_cards.clear()

    def validate_throw(self, card: Card) -> None:
        """Проверяет возможность подкинуть карту"""
        # Проверяем, не на столе ли уже карта
        all_cards = self._get_attack_cards() + self._get_defend_cards()
        if card in all_cards:
            raise CardAlreadyOnTableError(card)

        # Проверяем, есть ли место на столе
        if self.slots <= len(self.table_cards):
            raise NoFreeSlotsError()

        # Если стол не пустой, проверяем ранг
        if self.table_cards:
            table_ranks = self._get_table_ranks()
            if card.rank not in table_ranks:
                raise InvalidThrowError(str(card), [str(r) for r in table_ranks])

    def throw_card(self, card: Card) -> Dict:
        """Добавляет карту на стол"""
        # Проверяем возможность подкинуть карту
        self.validate_throw(card)
        
        # Если все проверки пройдены, добавляем карту
        self.table_cards.append({"attack_card": card, "defend_card": None})
        return {"status": "success", "message": "success"}
    
    def validate_defense(self, attack_card: Card, defend_card: Card) -> None:
        """Проверяет возможность защиты картой"""
        # Проверяем, что атакующая карта на столе
        if self._get_card_index(attack_card) is None:
            raise CardNotOnTableError(attack_card)

        # Проверяем масти
        if defend_card.suit != attack_card.suit:
            # Если защищающаяся карта не козырь - ошибка
            if not isinstance(defend_card, TrumpCard):
                raise InvalidDefenseError(attack_card=attack_card, defend_card=defend_card)
        else:
            # Если масти одинаковые, проверяем значение
            if not defend_card > attack_card:
                raise WeakDefenseError(attack_card=attack_card, defend_card=defend_card)

    def cover_card(self, attack_card: Card, defend_card: Card) -> bool:
        """Бьет карту на столе"""
        # Проверяем возможность защиты
        self.validate_defense(attack_card, defend_card)
        
        # Если все проверки пройдены, добавляем карту защиты
        idx = self._get_card_index(attack_card)
        if idx is not None:
            self.table_cards[idx]['defend_card'] = defend_card
            return True
        
        return False

    def get_all_cards(self) -> list[Card]:
        """Возвращает все карты на столе (и атакующие, и защитные)."""
        all_cards = []
        for pair in self.table_cards:
            if pair.get("attack_card"):
                all_cards.append(pair["attack_card"])
            if pair.get("defend_card"):
                all_cards.append(pair["defend_card"])
        return all_cards

