from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Integer
from bot.database import Base


class ExamScores(Base):
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    user: Mapped['Users'] = relationship(
        "Users",
        back_populates="exam_scores"
    )

    def __str__(self):
        return f"<Score {self.id}: {self.subject} {self.score}>"
