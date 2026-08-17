from sqlalchemy import String, Text, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin

class Service(Base, TimestampMixin):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    category: Mapped[str] = mapped_column(String(50), default="DP", index=True)
    name: Mapped[str] = mapped_column(String(255), index=True) # Removed unique=True to allow same service name in different companies
    description: Mapped[str | None] = mapped_column(Text)
    default_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)
    
    # Relationships
    company = relationship("Company", back_populates="services")
    invoice_items = relationship("InvoiceItem", back_populates="service", cascade="all, delete-orphan")
    quotation_items = relationship("QuotationItem", back_populates="service", cascade="all, delete-orphan")
