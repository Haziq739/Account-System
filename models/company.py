from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin

class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    ntn_number: Mapped[str | None] = mapped_column(String(100))
    gst_registration: Mapped[str | None] = mapped_column(String(100))
    tax_enabled: Mapped[bool] = mapped_column(default=False)
    default_tax_rate: Mapped[float] = mapped_column(default=0.0)
    logo_path: Mapped[str | None] = mapped_column(String(255))
    
    # Relationships
    invoices = relationship("Invoice", back_populates="company", cascade="all, delete-orphan")
    quotations = relationship("Quotation", back_populates="company", cascade="all, delete-orphan")
    users = relationship("User", back_populates="company")
    customers = relationship("Customer", back_populates="company", cascade="all, delete-orphan")
    services = relationship("Service", back_populates="company", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="company", cascade="all, delete-orphan")
    ledger_entries = relationship("CustomerLedger", back_populates="company", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="company", cascade="all, delete-orphan")
    vendors = relationship("Vendor", back_populates="company", cascade="all, delete-orphan")
    vendor_bills = relationship("VendorBill", back_populates="company", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="company", cascade="all, delete-orphan")
    employee_advances = relationship("EmployeeAdvance", back_populates="company", cascade="all, delete-orphan")
