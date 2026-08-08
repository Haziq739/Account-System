from sqlalchemy import String, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin

class Service(Base, TimestampMixin):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(50), default="DP", index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    default_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)
    
    # Relationships
    invoice_items = relationship("InvoiceItem", back_populates="service", cascade="all, delete-orphan")
    quotation_items = relationship("QuotationItem", back_populates="service", cascade="all, delete-orphan")
