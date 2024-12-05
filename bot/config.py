import os
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from pydantic_settings import BaseSettings, SettingsConfigDict

BASEDIR = os.path.dirname(os.path.abspath(__file__))  # Базовая директория проекта


class Settings(BaseSettings):
    # Основные настройки приложения, считываемые из .env файла
    BOT_TOKEN: str  # Токен Telegram-бота

    # Настройки для подключения к базе данных
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    DB_USER: str
    DB_PASS: str

    # Настройки логирования
    FORMAT_LOG: str = "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
    LOG_ROTATION: str = "10 MB"

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASEDIR, "..", ".env")  # Файл с переменными окружения
    )

    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


# Инициализация настроек приложения
settings = Settings()

# Инициализация бота и диспетчера
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),  # Используем Markdown для форматирования сообщений
)
dp = Dispatcher(storage=MemoryStorage())  # В качестве хранилища FSM используем память

# Настройка логирования с использованием ротации логов
log_file_path = os.path.join(BASEDIR, "..", "log.txt")  # Путь до файла логов
logger.add(
    log_file_path, format=settings.FORMAT_LOG, rotation=settings.LOG_ROTATION, retention="7 days", compression="zip"
)

# Получение строки подключения к базе данных
database_url = settings.DATABASE_URL
