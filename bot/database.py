from datetime import datetime
from sqlalchemy import Integer, func
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker, AsyncAttrs
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from bot.config import database_url

# Асинхронный движок для подключения к базе данных
engine = create_async_engine(database_url)

# Асинхронные сессии
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# Декоратор для автоматического создания и управления сессией базы данных
def connection(method):
    async def wrapper(*args, **kwargs):
        async with async_session_maker() as session:
            try:
                # Передаем сессию в метод
                return await method(*args, session=session, **kwargs)
            except Exception as e:
                await session.rollback()  # Откатываем транзакцию в случае ошибки
                raise e
            finally:
                await session.close()  # Закрываем сессию
    return wrapper


# Базовый класс для всех моделей базы данных
class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    @classmethod
    @property
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    def __repr__(self) -> str:
        """Строковое представление объекта для удобства отладки"""
        return f"<{self.__class__.__name__}(id={self.id}, created_at={self.created_at}, updated_at={self.updated_at})>"
