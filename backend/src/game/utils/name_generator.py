import random

ADJECTIVES_GLOSSARY = [
    "Быстрый", "Хитрый", "Веселый", "Смелый", "Мудрый", 
    "Ловкий", "Тихий", "Громкий", "Счастливый", "Загадочный",
    "Проворный", "Спокойный", "Яркий", "Темный", "Добрый"
]

NOUNS_GLOSSARY = [
    "Лис", "Волк", "Медведь", "Заяц", "Орел", 
    "Сокол", "Тигр", "Лев", "Кот", "Енот",
    "Дракон", "Феникс", "Грифон", "Змей", "Барс"
]

def generate_player_name() -> str:
    """Генерирует случайное имя игрока из прилагательного и существительного."""
    adjective = random.choice(ADJECTIVES_GLOSSARY)
    noun = random.choice(NOUNS_GLOSSARY)
    return f"{adjective}{noun}"

def generate_player_name_with_suffix() -> str:
    """Генерирует случайное имя игрока с числовым суффиксом для большей уникальности."""
    name = generate_player_name()
    suffix = random.randint(10, 99)
    return f"{name}{suffix}"

