from typing import List, Dict, Any
from sqlalchemy.orm import joinedload
from database.session import SessionLocal
from models.vendor_bill import VendorBill
from services.history import HistoryService
from datetime import date

class VendorBillService:
    
    @staticmethod
    def generate_bill_number(company_id: int) -> str:
        with SessionLocal() as s:
            from models.company import Company
            comp = s.query(Company).filter(Company.id == company_id).first()
            prefix = "BILL"
            if comp:
                if "RN Scanner" in comp.name:
                    prefix = "RNB"
                elif "K Dynamics" in comp.name:
                    prefix = "KDB"
            
            count = s.query(VendorBill).filter(VendorBill.company_id == company_id).count()
            seq = count + 1
            return f"{prefix}-{seq:03d}"

    @staticmethod
    def get_bills(company_id: int) -> List[Dict[str, Any]]:
        with SessionLocal() as s:
            bills = s.query(VendorBill).options(joinedload(VendorBill.vendor)).filter(
                VendorBill.company_id == company_id,
                VendorBill.is_deleted == False
            ).order_by(VendorBill.id.desc()).all()
            
            results = []
            for b in bills:
                results.append({
                    "id": b.id,
                    "bill_number": b.bill_number,
                    "vendor_id": b.vendor_id,
                    "vendor_name": b.vendor.name if b.vendor else "Unknown",
                    "description": b.description or "",
                    "amount": float(b.amount),
                    "bill_date": b.bill_date,
                    "created_at": b.created_at
                })
            return results

    @staticmethod
    def create_bill(
        company_id: int,
        vendor_id: int,
        description: str,
        amount: float,
        bill_date: date,
        user_id: int = None
    ) -> Dict[str, Any]:
        with SessionLocal() as s:
            bill_number = VendorBillService.generate_bill_number(company_id)
            
            new_bill = VendorBill(
                company_id=company_id,
                vendor_id=vendor_id,
                bill_number=bill_number,
                description=description,
                amount=amount,
                bill_date=bill_date
            )
            s.add(new_bill)
            s.commit()
            
            HistoryService.log_action(
                "create", "VendorBill", bill_number, 
                f"Created Vendor Bill {bill_number} for {amount}", user_id
            )
            
            # Automatically add to Day Book as an Expense
            from models.expense import Expense
            new_exp = Expense(
                company_id=company_id,
                vendor_id=vendor_id,
                title=f"Vendor Bill {bill_number}",
                amount=amount,
                expense_date=bill_date,
                notes=description
            )
            s.add(new_exp)
            s.commit()

            
            return {
                "id": new_bill.id,
                "bill_number": new_bill.bill_number
            }

    @staticmethod
    def update_bill(
        company_id: int,
        bill_id: int,
        vendor_id: int,
        description: str,
        amount: float,
        user_id: int = None
    ) -> bool:
        with SessionLocal() as s:
            b = s.query(VendorBill).filter(
                VendorBill.id == bill_id,
                VendorBill.company_id == company_id,
                VendorBill.is_deleted == False
            ).first()
            
            if not b:
                return False
                
            b.vendor_id = vendor_id
            b.description = description
            b.amount = amount
            s.commit()
            
            # Also update the corresponding Expense in Day Book
            from models.expense import Expense
            exp = s.query(Expense).filter(
                Expense.company_id == company_id,
                Expense.title == f"Vendor Bill {b.bill_number}",
                Expense.is_deleted == False
            ).first()
            
            if exp:
                exp.vendor_id = vendor_id
                exp.amount = amount
                exp.notes = description
                s.commit()
            
            HistoryService.log_action("update", "VendorBill", b.bill_number, f"Updated vendor bill {b.bill_number}", user_id)
            return True

    @staticmethod
    def delete_bill(company_id: int, bill_id: int, user_id: int = None) -> bool:
        with SessionLocal() as s:
            b = s.query(VendorBill).filter(
                VendorBill.id == bill_id,
                VendorBill.company_id == company_id,
                VendorBill.is_deleted == False
            ).first()
            
            if not b:
                return False
                
            b.is_deleted = True
            b_num = b.bill_number
            s.commit()
            
            # Also delete the corresponding Expense in Day Book
            from models.expense import Expense
            exp = s.query(Expense).filter(
                Expense.company_id == company_id,
                Expense.title == f"Vendor Bill {b_num}",
                Expense.is_deleted == False
            ).first()
            if exp:
                exp.is_deleted = True
                s.commit()
            
            HistoryService.log_action("delete", "VendorBill", b_num, f"Deleted vendor bill {b_num}", user_id)
            return True
