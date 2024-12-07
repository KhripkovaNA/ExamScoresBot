from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, func
from sqlalchemy.exc import SQLAlchemyError
from bot.database import Base
from loguru import logger

# Типовой параметр T с ограничением, что это наследник Base
T = TypeVar("T", bound=Base)


class BaseDAO(Generic[T]):
    """Базовый класс DAO для работы с моделями SQLAlchemy"""
    model: type[T]

    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int, session: AsyncSession):
        """Найти запись по ID"""
        logger.info(f"Поиск {cls.model.__name__} с ID: {data_id}")
        try:
            query = select(cls.model).filter_by(id=data_id)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record:
                logger.info(f"Запись {cls.model.__name__} с ID {data_id} найдена")
            else:
                logger.info(f"Запись {cls.model.__name__} с ID {data_id} не найдена")
            return record
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записи {cls.model.__name__} с ID {data_id}: {e}")
            raise

    @classmethod
    async def find_one_or_none(cls, session: AsyncSession, filters: BaseModel):
        """Найти одну запись по фильтрам"""
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.info(f"Поиск {cls.model.__name__} с фильтрами: {filter_dict}")
        try:
            query = select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record:
                logger.info(f"Запись {cls.model.__name__} найдена: {record}")
            else:
                logger.info(f"Запись {cls.model.__name__} не найдена по фильтрам: {filter_dict}")
            return record
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записи {cls.model.__name__} по фильтрам {filter_dict}: {e}")
            raise

    @classmethod
    async def find_all(cls, session: AsyncSession, filters: Optional[BaseModel] = None):
        """Найти все записи (с фильтром или без)"""
        filter_dict = filters.model_dump(exclude_unset=True) if filters else None
        logger.info(f"Поиск всех записей {cls.model.__name__} с фильтрами: {filter_dict}")
        try:
            query = select(cls.model) if not filter_dict else select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            records = result.scalars().all()
            logger.info(f"Найдено записей {cls.model.__name__}: {len(records)}")
            return records
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записей {cls.model.__name__} с фильтрами {filter_dict}: {e}")
            raise

    @classmethod
    async def add(cls, session: AsyncSession, values: BaseModel):
        """Добавить одну запись"""
        values_dict = values.model_dump(exclude_unset=True)
        logger.info(f"Добавление новой записи {cls.model.__name__} с данными: {values_dict}")
        try:
            new_instance = cls.model(**values_dict)
            session.add(new_instance)
            await session.commit()
            logger.info(f"Запись {cls.model.__name__} успешно добавлена: {new_instance}")
            return new_instance
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при добавлении записи {cls.model.__name__} с данными {values_dict}: {e}")
            raise

    @classmethod
    async def add_many(cls, session: AsyncSession, instances: List[BaseModel]):
        """Добавить несколько записей"""
        values_list = [item.model_dump(exclude_unset=True) for item in instances]
        logger.info(f"Добавление нескольких записей {cls.model.__name__}: {values_list}")
        try:
            new_instances = [cls.model(**values) for values in values_list]
            session.add_all(new_instances)
            await session.commit()
            logger.info(f"Успешно добавлено записей {cls.model.__name__}: {len(new_instances)}")
            return new_instances
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при добавлении записей {cls.model.__name__}: {e}")
            raise

    @classmethod
    async def update(cls, session: AsyncSession, filters: BaseModel, values: BaseModel):
        """Обновить записи по фильтрам"""
        filter_dict = filters.model_dump(exclude_unset=True)
        values_dict = values.model_dump(exclude_unset=True)
        logger.info(f"Обновление записей {cls.model.__name__} с фильтрами {filter_dict} и данными {values_dict}")
        try:
            query = (
                sqlalchemy_update(cls.model)
                .where(*[getattr(cls.model, k) == v for k, v in filter_dict.items()])
                .values(**values_dict)
                .execution_options(synchronize_session="fetch")
            )
            result = await session.execute(query)
            await session.commit()
            logger.info(f"Обновлено записей {cls.model.__name__}: {result.rowcount}")
            return result.rowcount
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при обновлении записей {cls.model.__name__}: {e}")
            raise

    @classmethod
    async def delete(cls, session: AsyncSession, filters: BaseModel):
        """Удалить записи по фильтрам"""
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.info(f"Удаление записей {cls.model.__name__} с фильтрами: {filter_dict}")
        if not filter_dict:
            logger.error("Удаление невозможно: не указан ни один фильтр")
            raise ValueError("Нужен хотя бы один фильтр для удаления")
        try:
            query = sqlalchemy_delete(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            await session.commit()
            logger.info(f"Удалено записей {cls.model.__name__}: {result.rowcount}")
            return result.rowcount
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при удалении записей {cls.model.__name__} с фильтрами {filter_dict}: {e}")
            raise
