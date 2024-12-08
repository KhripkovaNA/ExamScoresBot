from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.dispatcher.router import Router
from aiogram.fsm.context import FSMContext
from loguru import logger
from bot.config import bot
from bot.users.service import RegisterState, register_user, check_user, update_commands_based_on_registration, \
    check_name

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    """
    Хендлер для команды /start
    Проверяет пользователя и обновляет доступные команды
    """
    telegram_id = message.from_user.id
    logger.info(f"Команда /start от пользователя с Telegram ID: {telegram_id}")

    # Проверка пользователя
    existing_user = await check_user(telegram_id)
    if existing_user:
        # Обновление команд для зарегистрированного пользователя
        commands_updated = await update_commands_based_on_registration(bot, message.chat.id, True)
        if commands_updated:
            full_name = existing_user.full_name() or message.from_user.full_name or 'Пользователь'
            await message.answer(
                f"С возвращением, {full_name}!\n"
                "Вы уже зарегистрированы. Используйте команды /enter\\_scores и /view\\_scores для работы с баллами ЕГЭ"
            )
        else:
            await message.answer(
                "Вы уже зарегистрированы, но произошла ошибка при обновлении команд. "
                "Функционал может работать некорректно"
            )
    else:
        # Обновление команд для незарегистрированного пользователя
        commands_updated = await update_commands_based_on_registration(bot, message.chat.id, False)
        if commands_updated:
            await message.answer(
                "Добро пожаловать! Чтобы продолжить, пожалуйста, зарегистрируйтесь, используя команду /register"
            )
        else:
            await message.answer(
                "Произошла ошибка при обновлении команд. Функционал может работать некорректно"
            )


@router.message(Command("register"))
async def register_handler(message: Message, state: FSMContext):
    """
    Хендлер для команды /register
    Запускает процесс регистрации пользователя
    """
    telegram_id = message.from_user.id
    logger.info(f"Команда /register от пользователя {telegram_id}")

    # Проверка на уже зарегистрированного пользователя
    try:
        existing_user = await check_user(telegram_id)
        if existing_user:
            await message.answer(
                f"Вы уже зарегистрированы как {existing_user.full_name()}.\n"
                "Используйте команды /enter\\_scores и /view\\_scores для работы с баллами ЕГЭ"
            )
            logger.info(f"Пользователь {telegram_id} уже зарегистрирован")
            return
    except Exception as e:
        logger.error(f"Ошибка при проверке регистрации пользователя {telegram_id}: {e}")
        await message.answer("Ошибка при проверке данных. Попробуйте позже")
        return

    await message.answer("Введите ваше имя:")
    await state.set_state(RegisterState.waiting_for_first_name)


@router.message(RegisterState.waiting_for_first_name)
async def get_first_name(message: Message, state: FSMContext):
    """Обрабатывает введенное имя пользователя"""
    first_name = await check_name(message.text)
    if first_name:
        await state.update_data(first_name=first_name)
        logger.info(f"Пользователь {message.from_user.id} ввел имя: {first_name}")
        await message.answer("Теперь введите вашу фамилию:")
        await state.set_state(RegisterState.waiting_for_last_name)
    else:
        logger.warning(f"Пользователь {message.from_user.id} ввел некорректное имя")
        await message.answer("Некорректное имя. Попробуйте еще раз. Введите ваше имя:")


@router.message(RegisterState.waiting_for_last_name)
async def get_last_name(message: Message, state: FSMContext):
    """Обрабатывает введенную фамилию пользователя и завершает регистрацию"""
    last_name = await check_name(message.text)
    if last_name:
        data = await state.get_data()
        first_name = data["first_name"]
        telegram_id = message.from_user.id
        logger.info(f"Пользователь {telegram_id} ввел фамилию: {last_name}")

        try:
            # Сохранение данных пользователя
            await register_user(telegram_id, first_name, last_name)
            await update_commands_based_on_registration(bot, message.chat.id, True)  # Обновление команд

            await message.answer(
                f"Регистрация завершена!\n"
                f"Ваши данные:\nИмя: {first_name}\nФамилия: {last_name}"
            )
            logger.info(f"Пользователь {telegram_id} успешно зарегистрирован")
        except ValueError:
            await message.answer("Вы уже зарегистрированы. Используйте доступные команды")
            logger.info(f"Пользователь {telegram_id} попытался зарегистрироваться повторно")
        except Exception as e:
            logger.error(f"Ошибка при регистрации пользователя {telegram_id}: {e}")
            await message.answer("Произошла ошибка при регистрации. Попробуйте позже.")
        finally:
            await state.clear()

    else:
        logger.warning(f"Пользователь {message.from_user.id} ввел некорректную фамилию")
        await message.answer("Некорректная фамилия. Попробуйте еще раз. Введите вашу фамилию:")
