from sqlalchemy import String, ForeignKey, Date, Numeric, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin
from datetime import date

class EmployeeAdvance(Base, TimestampMixin):
    __tablename__ = "employee_advances"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    expense_id: Mapped[int | None] = mapped_column(ForeignKey("expenses.id"))
    
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    advance_date: Mapped[date] = mapped_column(Date, default=date.today)
    month: Mapped[str] = mapped_column(String(50)) # e.g., "August 2026"
    description: Mapped[str | None] = mapped_column(Text)
    
    is_cleared: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Relationships
    company = relationship("Company", back_populates="employee_advances")
    employee = relationship("Employee", back_populates="advances")
    expense = relationship("Expense")
