import logging
import sys

from backend.app.config.settings import DEBUG


def setup_logging():
    """
    Настраивает централизованное логирование для всего приложения.

    - Устанавливает уровень INFO для продакшена и DEBUG для разработки.
    - Использует единый формат для всех логов.
    - Выводит логи в sys.stdout.
    """
    log_level = logging.DEBUG if DEBUG else logging.INFO
    log_format = (
        "%(asctime)s - [%(levelname)s] - %(name)s - "
        "(%(filename)s).%(funcName)s(%(lineno)d): %(message)s"
    )

    # Получаем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Удаляем все существующие обработчики, чтобы избежать дублирования
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Создаем и настраиваем обработчик для вывода в консоль
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    formatter = logging.Formatter(log_format)
    stream_handler.setFormatter(formatter)

    root_logger.addHandler(stream_handler)

    logging.info("Система логирования успешно настроена.") 