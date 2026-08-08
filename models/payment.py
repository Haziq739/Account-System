from sqlalchemy import String, ForeignKey, Date, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin
from datetime import date

class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    receipt_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    is_advance: Mapped[bool] = mapped_column(default=False, server_default="0")
    payment_date: Mapped[date] = mapped_column(Date, default=date.today)
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    payment_method: Mapped[str] = mapped_column(String(50)) # cash, bank transfer, check
    reference_number: Mapped[str | None] = mapped_column(String(100)) # e.g., check number
    notes: Mapped[str | None] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)

    # Foreign Keys
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id"))

    # Relationships
    company = relationship("Company", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payments")
