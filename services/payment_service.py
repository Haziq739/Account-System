from typing import List, Dict, Any, Optional
from database.session import SessionLocal
from models.payment import Payment
from models.ledger import CustomerLedger
from models.invoice import Invoice
from models.company import Company
from models.customer import Customer
from services.history import HistoryService
from datetime import date
from sqlalchemy import desc

class PaymentService:
    
    @staticmethod
    def generate_receipt_number(company_id: int) -> str:
        with SessionLocal() as s:
            comp = s.query(Company).filter(Company.id == company_id).first()
            prefix = "REC"
            if comp:
                if "RN Scanner" in comp.name:
                    prefix = "RN-REC"
                elif "K Dynamics" in comp.name:
                    prefix = "KD-REC"
            
            count = s.query(Payment).filter(Payment.company_id == company_id).count()
            seq = count + 1
            return f"{prefix}-{seq:04d}"

    @staticmethod
    def create_payment(
        company_id: int,
        customer_id: int,
        amount: float,
        payment_method: str,
        payment_date: date,
        reference_number: str = "",
        notes: str = "",
        invoice_id: Optional[int] = None,
        user_id: int = 1,
        is_advance: bool = False
    ) -> Dict[str, Any]:
        with SessionLocal() as s:
            receipt = PaymentService.generate_receipt_number(company_id)
            pay = Payment(
                company_id=company_id,
                customer_id=customer_id,
                invoice_id=invoice_id,
                receipt_number=receipt,
                amount=amount,
                payment_method=payment_method,
                payment_date=payment_date,
                reference_number=reference_number,
                notes=notes,
                is_advance=is_advance
            )
            s.add(pay)
            
            # Update Invoice if linked
            invoice_ref = ""
            if invoice_id:
                inv = s.query(Invoice).filter(Invoice.id == invoice_id).first()
                if inv:
                    invoice_ref = inv.invoice_number
                    inv.paid_amount = float(inv.paid_amount) + amount
                    if float(inv.paid_amount) >= float(inv.net_amount):
                        inv.status = "paid"
                    elif float(inv.paid_amount) > 0:
                        inv.status = "partial"
                    else:
                        inv.status = "unpaid"
            
            s.flush()
            
            # Fetch latest balance
            latest_ledger = s.query(CustomerLedger).filter(
                CustomerLedger.company_id == company_id,
                CustomerLedger.customer_id == customer_id
            ).order_by(desc(CustomerLedger.id)).first()
            
            current_balance = float(latest_ledger.balance) if latest_ledger else 0.0
            new_balance = current_balance - float(amount) # Credit decreases balance
            
            desc_text = f"Payment Received: {receipt}"
            if invoice_ref:
                desc_text += f" for Invoice {invoice_ref}"
            else:
                if is_advance:
                    desc_text += " (Advance)"
                else:
                    desc_text += " (Unlinked)"
                    
            ledger_entry = CustomerLedger(
                company_id=company_id,
                customer_id=customer_id,
                transaction_date=payment_date,
                transaction_type="advance_payment" if is_advance else "payment",
                reference_id=receipt,
                credit=amount,
                debit=0.0,
                balance=new_balance,
                description=desc_text
            )
            s.add(ledger_entry)
            
            s.commit()
            
            HistoryService.log_action(
                "create", "Payment", receipt, 
                f"Received {amount} via {payment_method}", user_id
            )
            
            return {
                "id": pay.id,
                "receipt_number": pay.receipt_number,
                "amount": float(pay.amount),
                "is_advance": pay.is_advance
            }
            
    @staticmethod
    def get_payments(company_id: int) -> List[Dict[str, Any]]:
        with SessionLocal() as s:
            payments = s.query(Payment).filter(
                Payment.company_id == company_id,
                Payment.is_deleted == False
            ).order_by(desc(Payment.id)).all()
            
            results = []
            for p in payments:
                results.append({
                    "id": p.id,
                    "receipt_number": p.receipt_number,
                    "customer_name": p.customer.name if p.customer else "Unknown",
                    "payment_date": p.payment_date,
                    "amount": float(p.amount),
                    "payment_method": p.payment_method,
                    "invoice_number": p.invoice.invoice_number if p.invoice else "Advance"
                })
            return results
            
    @staticmethod
    def get_payments_by_invoice(invoice_id: int) -> List[Dict[str, Any]]:
        with SessionLocal() as s:
            payments = s.query(Payment).filter(
                Payment.invoice_id == invoice_id,
                Payment.is_deleted == False
            ).order_by(Payment.payment_date.asc(), Payment.id.asc()).all()
            
            results = []
            for p in payments:
                results.append({
                    "id": p.id,
                    "receipt_number": p.receipt_number,
                    "payment_date": p.payment_date,
                    "amount": float(p.amount),
                    "payment_method": p.payment_method,
                    "reference_number": p.reference_number,
                    "is_advance": p.is_advance
                })
            return results
            
    @staticmethod
    def soft_delete_payment(payment_id: int, user_id: int) -> bool:
        with SessionLocal() as s:
            pay = s.query(Payment).filter(Payment.id == payment_id).first()
            if not pay:
                return False
                
            pay.is_deleted = True
            
            latest_ledger = s.query(CustomerLedger).filter(
                CustomerLedger.company_id == pay.company_id,
                CustomerLedger.customer_id == pay.customer_id
            ).order_by(desc(CustomerLedger.id)).first()
            
            current_balance = float(latest_ledger.balance) if latest_ledger else 0.0
            new_balance = current_balance + float(pay.amount) # Reversing credit increases balance
            
            ledger_entry = CustomerLedger(
                company_id=pay.company_id,
                customer_id=pay.customer_id,
                transaction_date=date.today(),
                transaction_type="adjustment",
                reference_id=pay.receipt_number,
                credit=0.0,
                debit=float(pay.amount),
                balance=new_balance,
                description=f"Reversed Payment: {pay.receipt_number}"
            )
            s.add(ledger_entry)
            
            if pay.invoice:
                pay.invoice.paid_amount = float(pay.invoice.paid_amount) - float(pay.amount)
                if float(pay.invoice.paid_amount) <= 0:
                    pay.invoice.status = "unpaid"
                elif float(pay.invoice.paid_amount) < float(pay.invoice.net_amount):
                    pay.invoice.status = "partial"
            
            HistoryService.log_action(
                "delete", "Payment", pay.receipt_number, 
                f"Deleted payment {pay.receipt_number}", user_id
            )
            
            s.commit()
            return True
