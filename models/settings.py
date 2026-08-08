from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base, TimestampMixin

class Settings(Base, TimestampMixin):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
