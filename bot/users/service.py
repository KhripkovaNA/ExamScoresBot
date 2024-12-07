import re
from typing import Union
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.state import StatesGroup, State
from loguru import logger
from bot.database import connection
from bot.users.dao import UsersDAO
from bot.users.schemas import TelegramIDModel, TelegramUserModel


class RegisterState(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()


@connection
async def check_user(telegram_id: int, session: AsyncSession) -> TelegramUserModel | None:
    """Проверяет, существует ли пользователь с указанным Telegram ID"""
    try:
        logger.info(f"Проверка пользователя с Telegram ID: {telegram_id}")
        user = await UsersDAO.find_one_or_none(session, TelegramIDModel(telegram_id=telegram_id))
        return TelegramUserModel.model_validate(user) if user else None
    except Exception as e:
        logger.error(f"Ошибка при проверке пользователя с Telegram ID {telegram_id}: {e}")
        return None


async def update_commands_based_on_registration(bot: Bot, chat_id: Union[int, str], is_registered: bool) -> bool:
    """Обновляет доступные команды для пользователя в зависимости от статуса регистрации"""
    try:
        if is_registered:
            commands = [
                BotCommand(command="/enter_scores", description="Ввести баллы ЕГЭ"),
                BotCommand(command="/view_scores", description="Посмотреть баллы ЕГЭ"),
            ]
        else:
            commands = [
                BotCommand(command="register", description="Зарегистрироваться"),
            ]
        scope = BotCommandScopeChat(chat_id=chat_id)
        await bot.set_my_commands(commands, scope=scope)
        logger.info(f"Обновлены команды для чата {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении команд для чата {chat_id}: {e}")
        return False


async def check_name(name: str) -> str | None:
    """
    Проверяет корректность имени/фамилии.
    Условия:
    - Состоит только из букв, пробелов, дефисов или апострофов
    - Длина от 2 до 50 символов
    - Каждая часть имени (между дефисами или апострофами) начинается с заглавной буквы
    """
    name = name.strip()

    # Проверка длины имени
    if not (2 <= len(name) <= 50):
        return None

    # Регулярное выражение для проверки символов
    pattern = r"^[A-Za-zА-Яа-яЁёÀ-ÖØ-öø-ÿ'-]+$"
    if not re.fullmatch(pattern, name):
        return None

    # Разделение имени по дефису или апострофу и проверка каждой части
    parts = re.split(r"[-']", name)
    if any(len(part) < 2 for part in parts):  # Каждая часть должна быть минимум 2 символа
        return None

    # Преобразование каждой части в формат: первая буква заглавная
    formatted_name = "-".join(
        part.capitalize() if "-" in name else "'".join(p.capitalize() for p in parts)
        for part in parts
    )

    return formatted_name


@connection
async def register_user(telegram_id: int, first_name: str, last_name: str, session: AsyncSession) -> None:
    """Регистрация нового пользователя в базе данных"""
    try:
        user_data = TelegramUserModel(
            telegram_id=telegram_id, first_name=first_name, last_name=last_name
        )
        logger.info(f"Регистрация нового пользователя: {user_data}")
        await UsersDAO.add(session, user_data)
        logger.info(f"Пользователь {first_name} {last_name} (Telegram ID: {telegram_id}) успешно зарегистрирован")
    except IntegrityError:
        logger.warning(f"Пользователь с Telegram ID {telegram_id} уже существует в базе")
        raise ValueError("Пользователь уже зарегистрирован")
    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя {telegram_id}: {e}")
        raise
