from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.router import Router
from aiogram.fsm.context import FSMContext
from loguru import logger
from bot.config import bot
from bot.scores.keyboards import confirm_kb
from bot.users.service import RegisterState, register_user, check_user, update_commands_based_on_registration, \
    check_name, add_remove_cancel_command

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
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
            await message.answer(
                f"С возвращением, {existing_user.full_name()}!\n"
                "Вы уже зарегистрированы. Используйте команды /enter\\_scores и /view\\_scores "
                "для работы с баллами ЕГЭ\n"
                "Для редактирования аккаунта используйте команду /register"
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
                "Хотите изменить данные аккаунта?", reply_markup=confirm_kb()
            )

            logger.info(f"Пользователь {telegram_id} уже зарегистрирован")
            await state.set_state(RegisterState.waiting_for_confirmation_to_update)
            return
    except Exception as e:
        logger.error(f"Ошибка при проверке регистрации пользователя {telegram_id}: {e}")
        await add_remove_cancel_command(bot, message.chat.id, "remove")
        await state.clear()
        await message.answer("Ошибка при проверке данных. Попробуйте позже")
        return

    await message.answer("Введите ваше имя:")
    await add_remove_cancel_command(bot, message.chat.id, "add")
    await state.set_state(RegisterState.waiting_for_first_name)


@router.callback_query(RegisterState.waiting_for_confirmation_to_update)
async def handle_profile_update_confirmation(callback: CallbackQuery, state: FSMContext):
    """Подтверждает обновление имени и фамилии пользователя"""
    telegram_id = callback.from_user.id
    confirmation = callback.data

    try:
        if confirmation == "да":
            await add_remove_cancel_command(bot, callback.message.chat.id, "add")
            await callback.message.answer(f"Введите новое имя:")
            await state.update_data(update_profile=True)
            await state.set_state(RegisterState.waiting_for_first_name)
        elif confirmation == "нет":
            await callback.message.answer("Действие отменено")
            logger.info(f"Пользователь {telegram_id} отказался обновлять данные аккаунта")
            await state.clear()
        else:
            await callback.message.answer(
                "Ответ не распознан.\n"
                f"Хотите изменить данные аккаунта?",
                reply_markup=confirm_kb()
            )
    except Exception as e:
        logger.error(f"Ошибка при подтверждении обновления для пользователя {telegram_id}: {e}")
        await add_remove_cancel_command(bot, callback.message.chat.id, "remove")
        await state.clear()
        await callback.message.answer("Произошла ошибка. Попробуйте снова позже")


@router.message(RegisterState.waiting_for_first_name)
async def get_first_name(message: Message, state: FSMContext):
    """Обрабатывает введенное имя пользователя"""
    if message.text.startswith("/"):
        await cancel_handler(message, state)
        return
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
    if message.text.startswith("/"):
        await cancel_handler(message, state)
        return
    last_name = await check_name(message.text)
    if last_name:
        data = await state.get_data()
        update_profile = data.get("update_profile", False)
        first_name = data["first_name"]
        telegram_id = message.from_user.id
        logger.info(f"Пользователь {telegram_id} ввел фамилию: {last_name}")

        try:
            # Сохранение данных пользователя
            await register_user(telegram_id, first_name, last_name, update=update_profile)
            await update_commands_based_on_registration(bot, message.chat.id, True)  # Обновление команд
            message_include = "Аккаунт обновлен!\nВаши новые данные:" if update_profile \
                else "Регистрация завершена!\nВаши данные:\n"
            await message.answer(
                f"{message_include}Имя: {first_name}\nФамилия: {last_name}"
            )
            logger.info(f"Пользователь {telegram_id} успешно зарегистрирован или обновлен")

        except ValueError as e:
            # Обработка ошибки, если пользователь уже существует
            if update_profile:
                logger.error(f"Ошибка обновления данных пользователя {telegram_id}: {e}")
                await message.answer("Не удалось обновить данные. Попробуйте позже")
            else:
                logger.warning(f"Пользователь {telegram_id} попытался зарегистрироваться повторно")
                await message.answer("Произошла ошибка при регистрации. Попробуйте позже")
        except Exception as e:
            logger.error(f"Ошибка при регистрации пользователя {telegram_id}: {e}")
            await message.answer("Произошла ошибка при регистрации. Попробуйте позже")
        finally:
            await add_remove_cancel_command(bot, message.chat.id, "remove")
            await state.clear()

    else:
        logger.warning(f"Пользователь {message.from_user.id} ввел некорректную фамилию")
        await message.answer("Некорректная фамилия. Попробуйте еще раз. Введите вашу фамилию:")


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    """Обрабатывает отмену текущего действия"""
    current_state = await state.get_state()
    logger.info(f"Текущее состояние: {current_state}")
    if current_state:
        await state.clear()
        await message.answer("Действие отменено. Вы можете начать заново")
        await add_remove_cancel_command(bot, message.chat.id, "remove")
    else:
        await message.answer("Нет активного действия для отмены")
