import logging
from logging.handlers import RotatingFileHandler
import os
import sys

from backend.src.settings import AppSettings


settings = AppSettings()


def setup_logging():
    """
    Настраивает централизованное логирование для всего приложения.

    - Устанавливает уровень INFO для продакшена и DEBUG для разработки.
    - Использует единый формат для всех логов.
    - Выводит логи в sys.stdout.
    """
    match settings.environment:
        case "development":
            log_level = logging.DEBUG
        case "production":
            log_level = logging.WARNING
        case "staging":
            log_level = logging.INFO
        case _:
            log_level = logging.INFO

    log_format = (
        "[%(asctime)s] [%(levelname)s] [%(name)s] [PID:%(process)d]: %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    formatter = logging.Formatter(log_format)

    os.makedirs("logs", exist_ok=True)
    # обработчик вывода в файл
    file_handler = RotatingFileHandler(
        filename="logs/app.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # обработчик вывода в консоль
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    if settings.environment != "production":
        root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    logging.info("Система логирования успешно настроена.")
