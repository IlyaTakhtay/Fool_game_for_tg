# В начале файла или в отдельном модуле errors.py
class CardGameError(Exception):
    """Базовый класс для всех ошибок карточной игры"""
    pass

class CardNotOnTableError(CardGameError):
    """Ошибка: попытка взаимодействия с картой, которой нет на столе"""
    def __init__(self, card=None, message=None):
        self.card = card
        self.message = message or f"Карта {card} отсутствует на столе"
        super().__init__(self.message)
