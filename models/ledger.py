from sqlalchemy import String, ForeignKey, Date, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin
from datetime import date

class CustomerLedger(Base, TimestampMixin):
    __tablename__ = "customer_ledger"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_date: Mapped[date] = mapped_column(Date, default=date.today)
    transaction_type: Mapped[str] = mapped_column(String(50)) # invoice, payment, refund, adjustment
    reference_id: Mapped[str | None] = mapped_column(String(100)) # invoice number or payment receipt
    debit: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    credit: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    balance: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    description: Mapped[str | None] = mapped_column(Text)

    # Foreign Keys
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"))

    # Relationships
    company = relationship("Company", back_populates="ledger_entries")
    customer = relationship("Customer", back_populates="ledger_entries")
