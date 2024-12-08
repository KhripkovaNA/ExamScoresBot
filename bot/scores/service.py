from typing import Tuple, List
from aiogram.fsm.state import StatesGroup, State
from difflib import get_close_matches
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database import connection
from bot.scores.dao import ExamScoresDAO
from bot.scores.models import ExamScores
from bot.scores.schemas import UserExamScoreModel, UserSubjectModel, ScoreModel, ExamScoreID, UserIDModel
from bot.users.dao import UsersDAO
from bot.users.models import Users
from bot.users.schemas import TelegramIDModel

EXAM_SUBJECTS = [
    "Русский язык",
    "Математика (базовая)",
    "Математика (профильная)",
    "Обществознание",
    "История",
    "Английский язык",
    "Немецкий язык",
    "Французский язык",
    "Испанский язык",
    "Литература",
    "География",
    "Физика",
    "Химия",
    "Биология",
    "Информатика",
]


class EnterScoreState(StatesGroup):
    waiting_for_subject = State()
    waiting_for_confirmation = State()
    waiting_for_confirmation_to_update = State()
    waiting_for_score = State()


def check_subject(subject_entered: str) -> List[str]:
    """Ищет подходящие предметы по введенному тексту"""
    matching_subjects = [subject for subject in EXAM_SUBJECTS if subject_entered.lower() in subject.lower()]
    if not matching_subjects:
        matching_subjects = get_close_matches(subject_entered, EXAM_SUBJECTS, n=3, cutoff=0.3)
    return matching_subjects


async def check_user_score(
        telegram_id: int, subject: str, session: AsyncSession
) -> Tuple[Users | None, ExamScores | None]:

    user = await UsersDAO.find_one_or_none(session, TelegramIDModel(telegram_id=telegram_id))
    if not user:
        return None, None

    user_score = await ExamScoresDAO.find_one_or_none(
        session, filters=UserSubjectModel(user_id=user.id, subject=subject)
    )
    return user, user_score


@connection
async def get_existing_score(telegram_id: int, subject: str, session: AsyncSession) -> UserExamScoreModel | None:
    """Проверяет наличие предмета и оценки у пользователя с указанным Telegram ID"""
    try:
        user, result = await check_user_score(telegram_id, subject, session)
        if not user:
            logger.warning(f"Пользователь с Telegram ID {telegram_id} не найден")
            return None

        if result:
            return UserExamScoreModel(user_id=user.id, subject=result.subject, score=result.score)
        return None

    except Exception as e:
        logger.error(f"Ошибка при получении данных из БД для пользователя {telegram_id}: {e}")
        raise


def validate_score(score: str) -> bool:
    """Проверяет, что балл является числом от 0 до 100"""
    if score.isdigit():
        if 0 <= int(score) <= 100:
            return True

    return False


@connection
async def save_score(telegram_id: int, subject: str, score: int, session: AsyncSession) -> bool:
    """Сохраняет или обновляет балл для указанного предмета"""
    try:
        user, existing_score = await check_user_score(telegram_id, subject, session)
        if not user:
            logger.warning(f"Пользователь с Telegram ID {telegram_id} не найден")

        if existing_score:
            # Обновляем балл, если запись найдена
            updated_count = await ExamScoresDAO.update(
                session, filters=ExamScoreID(id=existing_score.id),
                values=ScoreModel(score=score)
            )
            if updated_count > 0:
                logger.info(f"Балл для предмета '{subject}' обновлен для пользователя {user.id}. Новый балл: {score}")
                return True
            else:
                logger.info(f"Не удалось обновить балл для предмета '{subject}' пользователя {user.id}")

        else:
            # Создаем новую запись, если её нет
            new_score_schema = UserExamScoreModel(user_id=user.id, subject=subject, score=score)
            new_score = await ExamScoresDAO.add(session, new_score_schema)
            if new_score:
                logger.info(f"Создание нового балла для предмета '{subject}' у пользователя {user.id}. Балл: {score}")
                return True

        return False

    except Exception as e:
        logger.error(f"Ошибка при сохранении балла для пользователя {telegram_id} и предмета '{subject}': {e}")
        return False


@connection
async def get_exam_scores(telegram_id: int, session: AsyncSession) -> List[UserExamScoreModel] | None:
    """Получает список баллов пользователя по всем предметам"""
    try:
        user = await UsersDAO.find_one_or_none(session, TelegramIDModel(telegram_id=telegram_id))
        if not user:
            logger.warning(f"Пользователь с Telegram ID {telegram_id} не найден")
            return None

        scores = await ExamScoresDAO.find_all(session, filters=UserIDModel(user_id=user.id))
        return [UserExamScoreModel.model_validate(score) for score in scores] if scores else None

    except Exception as e:
        logger.error(f"Ошибка при получении баллов для пользователя {telegram_id}: {e}")
        return None


def format_table(scores: List[UserExamScoreModel]) -> str:
    # Формируем таблицу с выравниванием
    scores_list = "\n".join(
        [f"{score.subject:<25}|{score.score:>6}" for score in scores]
    )

    return "Ваши баллы:\n\n"\
           "```\n"\
           f"{'Предмет':<25}|{'Балл':>6}\n"\
           f"{'-' * 32}\n"\
           f"{scores_list}"\
           "```"

