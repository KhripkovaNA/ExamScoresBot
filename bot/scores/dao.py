from bot.dao.base import BaseDAO
from bot.scores.models import ExamScores


class ExamScoresDAO(BaseDAO):
    model = ExamScores
