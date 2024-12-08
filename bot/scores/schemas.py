from pydantic import BaseModel, ConfigDict, Field


class ExamScoreID(BaseModel):
    id: int = Field(..., gt=0, description="Уникальный ID балла ЕГЭ")


class UserIDModel(BaseModel):
    user_id: int = Field(..., gt=0, description="Уникальный ID пользователя")

    # Конфигурация модели для поддержки ORM и работы с объектами
    model_config = ConfigDict(from_attributes=True)


class UserSubjectModel(UserIDModel):
    subject: str = Field(..., description="Название предмета")


class ScoreModel(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Балл от 0 до 100")


class UserExamScoreModel(UserSubjectModel, ScoreModel):
    pass
