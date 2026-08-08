from sqlalchemy import String, ForeignKey, Date, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin
from datetime import date

class Expense(Base, TimestampMixin):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    expense_date: Mapped[date] = mapped_column(Date, default=date.today)
    notes: Mapped[str | None] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)

    # Foreign Keys
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", name="fk_expense_customer"))
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id", name="fk_expense_vendor"))
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", name="fk_expense_employee"))
    
    # Relationships
    company = relationship("Company", back_populates="expenses")
    customer = relationship("Customer")
    vendor = relationship("Vendor")
    employee = relationship("Employee")
