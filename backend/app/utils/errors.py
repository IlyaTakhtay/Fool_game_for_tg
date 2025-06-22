# В начале файла или в отдельном модуле errors.py
class CardGameError(Exception):
    """Базовый класс для всех ошибок карточной игры"""
    pass

class GameLogicError(CardGameError):
    """Ошибка игровой логики"""
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class CardNotOnTableError(CardGameError):
    """Ошибка: попытка взаимодействия с картой, которой нет на столе"""
    def __init__(self, card=None, message=None):
        self.card = card
        self.message = message or f"Карта {card} отсутствует на столе"
        super().__init__(self.message)

class InvalidDefenseError(GameLogicError):
    """Ошибка: некорректная защита"""
    def __init__(self, attack_card, defend_card):
        message = f"Нельзя бить карту {attack_card} картой {defend_card} (разные масти)"
        super().__init__(message=message, error_code="INVALID_DEFENSE_SUIT")

class WeakDefenseError(GameLogicError):
    """Ошибка: карта слишком слабая для защиты"""
    def __init__(self, attack_card, defend_card):
        message = f"Нельзя бить карту {attack_card} картой {defend_card} (значение слишком мало)"
        super().__init__(message=message, error_code="INVALID_DEFENSE_VALUE")

class InvalidThrowError(GameLogicError):
    """Ошибка: нельзя подкинуть карту"""
    def __init__(self, card: str, table_ranks: list):
        if not table_ranks:
            message = "Нельзя подкинуть карту, когда стол пуст"
        else:
            ranks_str = ", ".join(str(r) for r in table_ranks)
            message = f"Можно подкидывать только карты со значением: {ranks_str}"
        super().__init__(message=message, error_code="INVALID_THROW_RANK")

class CardAlreadyOnTableError(GameLogicError):
    """Ошибка: карта уже на столе"""
    def __init__(self, card):
        message = f"Карта {card} уже на столе"
        super().__init__(message=message, error_code="CARD_ALREADY_ON_TABLE")

class NoFreeSlotsError(GameLogicError):
    """Ошибка: нет свободных слотов на столе"""
    def __init__(self):
        message = "На столе нет свободных мест для карт"
        super().__init__(message=message, error_code="NO_FREE_SLOTS")

class WrongTurnError(GameLogicError):
    """Ошибка: действие в неправильную фазу хода"""
    def __init__(self, current_role: str, attempted_action: str):
        message = f"Сейчас ваша роль - {current_role}. Вы не можете {attempted_action}."
        super().__init__(message=message, error_code="WRONG_TURN_ACTION")
