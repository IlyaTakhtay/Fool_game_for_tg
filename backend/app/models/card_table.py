from typing import List, Dict

from backend.app.models.card import Card, TrumpCard

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

    def clear_table(self) -> None:
        self.table_cards.clear()

    def throw_card(self, card: Card) -> Dict|Exception:
        """добавляет карту на стол"""
        all_cards = self._get_attack_cards() + self._get_defend_cards()
        if card in all_cards:
            raise ValueError("This card is on table") #todo custom error
        if (any(card.rank == table_card.rank for table_card in all_cards) 
            or len(self.table_cards) == 0):
            if self.slots > len(self.table_cards):
                self.table_cards.append({"attack_card": card, "defend_card": None})
                return {"status": "sucsess", "message": "sucsess"}
            else:
                {"status": "failed", "message": "no free slots"}
        return {"status": "failed", "message": "wrong rank"}
    
    def cover_card(self, card: Card, cover_card: Card) -> bool|ValueError:
        """Бьет карту на столе"""    
        if cover_card > card:
            idx = self._get_card_index(card)
            if idx is not None:
                self.table_cards[idx]['defend_card'] = cover_card
                return True
            else:
                raise ValueError("This card not on table") #todo custom error
        return False

