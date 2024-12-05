from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String
from typing import List
from bot.database import Base


class Users(Base):

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    exam_scores: Mapped[List["ExamScores"]] = relationship(
        "ExamScores",
        back_populates="user",
        cascade="all, delete-orphan"
    )

