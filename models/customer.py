from sqlalchemy import String, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin

class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    company_name: Mapped[str | None] = mapped_column(String(255))
    customer_type: Mapped[str] = mapped_column(String(50), default="regular", server_default="regular")
    is_deleted: Mapped[bool] = mapped_column(default=False)
    
    # Relationships
    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")
    quotations = relationship("Quotation", back_populates="customer", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")
    ledger_entries = relationship("CustomerLedger", back_populates="customer", cascade="all, delete-orphan")
