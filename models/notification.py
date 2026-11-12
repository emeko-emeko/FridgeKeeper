from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, utcnow


class NotificationLog(Base):
    """Какие уровни уведомлений (24/12/6/2 ч) уже обработаны для продукта."""

    __tablename__ = "notification_log"
    __table_args__ = (
        UniqueConstraint("product_id", "level_hours", name="uq_notification_product_level"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    level_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)  # "sent" | "skipped"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)