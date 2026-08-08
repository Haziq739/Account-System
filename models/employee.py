from sqlalchemy import String, Text, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin

class Employee(Base, TimestampMixin):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    
    name: Mapped[str] = mapped_column(String(100), index=True)
    salary: Mapped[float] = mapped_column(Numeric(12, 2))
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)
    
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)

    # Relationships
    company = relationship("Company", back_populates="employees")
    advances = relationship("EmployeeAdvance", back_populates="employee", cascade="all, delete-orphan")
