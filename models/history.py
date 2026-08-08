from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base
from datetime import datetime, timezone

class HistoryLog(Base):
    __tablename__ = "history_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(100)) # create, update, delete
    entity_type: Mapped[str] = mapped_column(String(100)) # e.g., Invoice, Customer
    entity_id: Mapped[int] = mapped_column(String(100))
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Foreign Keys
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
