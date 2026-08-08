from sqlalchemy import String, ForeignKey, Date, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin
from datetime import date
from typing import List

class Quotation(Base, TimestampMixin):
    __tablename__ = "quotations"

    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    issue_date: Mapped[date] = mapped_column(Date, default=date.today)
    valid_until: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), default="pending") # pending, converted
    
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    discount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    tax_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    tax_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    net_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    
    notes: Mapped[str | None] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)
    
    # Foreign Keys
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))

    # Relationships
    company = relationship("Company", back_populates="quotations")
    customer = relationship("Customer", back_populates="quotations")
    items: Mapped[List["QuotationItem"]] = relationship("QuotationItem", back_populates="quotation", cascade="all, delete-orphan")


class QuotationItem(Base, TimestampMixin):
    __tablename__ = "quotation_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_id: Mapped[int] = mapped_column(ForeignKey("quotations.id", ondelete="CASCADE"))
    service_id: Mapped[int | None] = mapped_column(ForeignKey("services.id"))
    description: Mapped[str] = mapped_column(Text)
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), default=1.0)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    total_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)

    # Relationships
    quotation = relationship("Quotation", back_populates="items")
    service = relationship("Service", back_populates="quotation_items")
