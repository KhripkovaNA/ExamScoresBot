from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.router import Router
from aiogram.fsm.context import FSMContext
from loguru import logger
from bot.scores.keyboards import choose_subject_kb, confirm_kb
from bot.scores.service import EnterScoreState, check_subject, EXAM_SUBJECTS, get_existing_score, save_score, \
    validate_score, get_exam_scores, format_table
from bot.users.service import check_user

router = Router()


@router.message(Command("enter_scores"))
async def enter_score_handler(message: Message, state: FSMContext):
    """
    Хендлер для команды /enter_scores
    Запускает процесс добавления или изменения баллов
    """
    telegram_id = message.from_user.id
    logger.info(f"Команда /enter_scores от пользователя {telegram_id}")

    # Проверяем, зарегистрирован ли пользователь
    try:
        if not await check_user(telegram_id):
            await message.answer(
                "Вы не зарегистрированы.\n"
                "Используйте команду /register для регистрации в системе"
            )
            logger.warning(f"Пользователь {telegram_id} не зарегистрирован")
            return

        await message.answer("Введите название предмета:")
        await state.set_state(EnterScoreState.waiting_for_subject)
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /enter_scores для пользователя {telegram_id}: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова позже")


@router.message(EnterScoreState.waiting_for_subject)
async def handle_subject_input(message: Message, state: FSMContext):
    """Обрабатывает введенное название предмета"""
    telegram_id = message.from_user.id
    subject_entered = message.text.strip()

    try:
        matching_subjects = check_subject(subject_entered)
        if not matching_subjects:
            await message.answer("Не удалось определить предмет. Попробуйте еще раз")
            logger.info(f"Предмет '{subject_entered}' не найден для пользователя {telegram_id}")
            return

        subject_kb = choose_subject_kb(matching_subjects)
        if len(matching_subjects) == 1:
            await message.answer("Подтвердите выбранный предмет:", reply_markup=subject_kb)
        else:
            await message.answer("Выберите подходящий предмет из списка:", reply_markup=subject_kb)
        await state.set_state(EnterScoreState.waiting_for_confirmation)
    except Exception as e:
        logger.error(f"Ошибка при обработке предмета '{subject_entered}' для пользователя {telegram_id}: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова позже")
        await state.clear()


@router.callback_query(EnterScoreState.waiting_for_confirmation)
async def handle_subject_choice(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор предмета из инлайн-клавиатуры
    Проверяет наличие балла в базе и запрашивает действие
    """
    telegram_id = callback.from_user.id
    selected_subject = callback.data

    try:
        if selected_subject == "Отмена":
            await callback.message.answer("Действие отменено")
            logger.info(f"Пользователь {telegram_id} отменил ввод предмета")
            await state.clear()
            return

        if selected_subject not in EXAM_SUBJECTS:
            await callback.message.answer("Выбранный предмет отсутствует в системе. Попробуйте снова")
            logger.warning(f"Некорректный выбор предмета '{selected_subject}' от пользователя {telegram_id}")
            await state.clear()
            return

        existing_score = await get_existing_score(telegram_id, selected_subject)
        if existing_score:
            await callback.message.answer(
                f"Для предмета {selected_subject} уже есть балл: {existing_score.score}.\n"
                "Вы хотите изменить балл?",
                reply_markup=confirm_kb()
            )
            await state.update_data(subject=selected_subject)
            await state.set_state(EnterScoreState.waiting_for_confirmation_to_update)
        else:
            await callback.message.answer(f"Введите балл для предмета {selected_subject}:")
            await state.update_data(subject=selected_subject)
            await state.set_state(EnterScoreState.waiting_for_score)

    except Exception as e:
        logger.error(f"Ошибка при выборе предмета '{selected_subject}' для пользователя {telegram_id}: {e}")
        await callback.answer("Произошла ошибка. Попробуйте снова позже")
        await state.clear()


@router.callback_query(EnterScoreState.waiting_for_confirmation_to_update)
async def handle_update_confirmation(callback: CallbackQuery, state: FSMContext):
    """Подтверждает обновление балла для предмета"""
    telegram_id = callback.from_user.id
    confirmation = callback.data
    data = await state.get_data()
    selected_subject = data.get("subject")

    try:
        if confirmation == "да":
            await callback.message.answer(f"Введите новый балл для предмета {selected_subject}:")
            await state.set_state(EnterScoreState.waiting_for_score)
        elif confirmation == "нет":
            await callback.message.answer("Действие отменено")
            logger.info(f"Пользователь {telegram_id} отказался обновлять балл для '{selected_subject}'")
            await state.clear()
        else:
            await callback.message.answer(
                "Ответ не распознан.\n"
                f"Вы хотите изменить балл предмета {selected_subject}?",
                reply_markup=confirm_kb()
            )
    except Exception as e:
        logger.error(f"Ошибка при подтверждении обновления для пользователя {telegram_id}: {e}")
        await callback.message.answer("Произошла ошибка. Попробуйте снова позже")
        await state.clear()


@router.message(EnterScoreState.waiting_for_score)
async def handle_score_input(message: Message, state: FSMContext):
    """Сохраняет или обновляет балл для выбранного предмета"""
    telegram_id = message.from_user.id
    score = message.text.strip()

    try:
        if not validate_score(score):
            await message.answer("Балл должен быть числом от 0 до 100. Попробуйте снова")
            logger.warning(f"Некорректный ввод балла '{score}' от пользователя {telegram_id}")
            return

        data = await state.get_data()
        selected_subject = data.get("subject")

        success = await save_score(telegram_id, selected_subject, int(score))
        if success:
            await message.answer(f"Балл {score} для предмета {selected_subject} успешно сохранен")
            logger.info(f"Пользователь {telegram_id} сохранил балл {score} для '{selected_subject}'")
        else:
            await message.answer("Ошибка при сохранении балла. Попробуйте позже")
            logger.error(
                f"Ошибка сохранения балла {score} для пользователя {telegram_id} и предмета {selected_subject}"
            )
    except Exception as e:
        logger.error(f"Ошибка при вводе балла для пользователя {telegram_id}: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова позже")
    finally:
        await state.clear()


@router.message(Command("view_scores"))
async def view_scores_handler(message: Message):
    """Хендлер для команды /view_scores"""
    telegram_id = message.from_user.id
    logger.info(f"Команда /view_scores от пользователя {telegram_id}")

    try:
        # Проверяем, зарегистрирован ли пользователь
        if not await check_user(telegram_id):
            await message.answer(
                "Вы не зарегистрированы.\n"
                "Используйте команду /register для регистрации в системе"
            )
            logger.warning(f"Пользователь {telegram_id} не зарегистрирован")
            return

        # Получаем баллы пользователя
        exam_scores = await get_exam_scores(telegram_id)
        if exam_scores:
            # Формируем ответ в виде таблицы
            await message.answer(format_table(exam_scores))
        else:
            await message.answer("У вас пока нет сохраненных баллов")
            logger.info(f"У пользователя {telegram_id} нет сохраненных баллов")
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /view_scores для пользователя {telegram_id}: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова позже")
