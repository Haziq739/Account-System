from sqlalchemy import String, Text, ForeignKey, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base, TimestampMixin
from datetime import date

class VendorBill(Base, TimestampMixin):
    __tablename__ = "vendor_bills"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    
    bill_number: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    bill_date: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)

    # Relationships
    company = relationship("Company", back_populates="vendor_bills")
    vendor = relationship("Vendor", back_populates="vendor_bills")
