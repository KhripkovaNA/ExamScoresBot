from pydantic import BaseModel, ConfigDict, Field


class TelegramIDModel(BaseModel):
    telegram_id: int = Field(..., gt=0, description="Уникальный ID пользователя Telegram (должен быть положительным)")

    # Конфигурация модели для поддержки ORM и работы с объектами
    model_config = ConfigDict(from_attributes=True)


class UserModel(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100, description="Имя пользователя")
    last_name: str = Field(..., min_length=1, max_length=100, description="Фамилия пользователя")

    # Конфигурация модели для поддержки ORM и работы с объектами
    model_config = ConfigDict(from_attributes=True)


class TelegramUserModel(TelegramIDModel, UserModel):
    def full_name(self) -> str:
        """Возвращает полное имя пользователя"""
        return f"{self.first_name} {self.last_name}"
