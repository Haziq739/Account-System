from typing import List, Dict, Any
from sqlalchemy import func
from database.session import SessionLocal
from models.invoice import Invoice, InvoiceItem
from services.history import HistoryService
from datetime import date

class InvoiceService:
    
    @staticmethod
    def generate_invoice_number(company_id: int) -> str:
        with SessionLocal() as s:
            from models.company import Company
            comp = s.query(Company).filter(Company.id == company_id).first()
            prefix = "INV"
            if comp:
                if "RN Scanner" in comp.name:
                    prefix = "RN"
                elif "K Dynamics" in comp.name:
                    prefix = "KD"
            
            count = s.query(Invoice).filter(Invoice.company_id == company_id).count()
            seq = count + 1
            return f"{prefix}-{seq:03d}"

    @staticmethod
    def get_invoices(company_id: int, context: str = "regular") -> List[Dict[str, Any]]:
        with SessionLocal() as s:
            from sqlalchemy.orm import joinedload
            query = s.query(Invoice).options(joinedload(Invoice.customer)).filter(
                Invoice.company_id == company_id,
                Invoice.is_deleted == False
            )
            if context == "regular":
                query = query.filter(Invoice.customer.has(customer_type="regular"))
            else:
                query = query.filter(Invoice.customer.has(customer_type="day_book"))
                
            invoices = query.order_by(Invoice.id.desc()).all()
            
            results = []
            for inv in invoices:
                results.append({
                    "id": inv.id,
                    "invoice_number": inv.invoice_number,
                    "category": inv.category,
                    "customer_id": inv.customer_id,
                    "customer_name": inv.customer.name if inv.customer else "Unknown",
                    "issue_date": inv.issue_date,
                    "net_amount": float(inv.net_amount),
                    "paid_amount": float(inv.paid_amount),
                    "status": inv.status,
                })
            return results

    @staticmethod
    def create_invoice(
        company_id: int,
        customer_id: int,
        issue_date: date,
        items: List[Dict[str, Any]], 
        discount: float,
        tax_percentage: float,
        paid_amount: float,
        payment_method: str,
        notes: str,
        user_id: int
    ) -> Dict[str, Any]:
        
        with SessionLocal() as s:
            invoice_number = InvoiceService.generate_invoice_number(company_id)
            
            # Calculate totals
            total_amount = sum(item["quantity"] * item["unit_price"] for item in items)
            tax_amount = (total_amount - discount) * (tax_percentage / 100.0)
            net_amount = (total_amount - discount) + tax_amount
            
            # Determine status
            if paid_amount >= net_amount:
                status = "paid"
            elif paid_amount > 0:
                status = "partial"
            else:
                status = "unpaid"
                
            inv = Invoice(
                invoice_number=invoice_number,
                company_id=company_id,
                customer_id=customer_id,
                category="GENERAL",
                issue_date=issue_date,
                total_amount=total_amount,
                discount=discount,
                tax_percentage=tax_percentage,
                tax_amount=tax_amount,
                net_amount=net_amount,
                paid_amount=paid_amount,
                payment_method=payment_method,
                status=status,
                notes=notes
            )
            s.add(inv)
            s.flush() # Get invoice ID
            
            # Add items
            for item in items:
                inv_item = InvoiceItem(
                    invoice_id=inv.id,
                    service_id=item["service_id"],
                    description=item["description"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    total_price=item["quantity"] * item["unit_price"]
                )
                s.add(inv_item)
                
            # Log invoice to Ledger
            from models.ledger import CustomerLedger
            from sqlalchemy import desc
            
            latest_ledger = s.query(CustomerLedger).filter(
                CustomerLedger.company_id == company_id,
                CustomerLedger.customer_id == customer_id
            ).order_by(desc(CustomerLedger.id)).first()
            
            current_balance = float(latest_ledger.balance) if latest_ledger else 0.0
            new_balance = current_balance + net_amount
            
            ledger_entry = CustomerLedger(
                company_id=company_id,
                customer_id=customer_id,
                transaction_date=issue_date,
                transaction_type="invoice",
                reference_id=invoice_number,
                credit=0.0,
                debit=net_amount,
                balance=new_balance,
                description=f"Invoice Generated: {invoice_number}"
            )
            s.add(ledger_entry)
            
            # Defer payment status and amount to PaymentService if paid
            inv.paid_amount = 0.0
            inv.status = "unpaid"
                
            s.commit()
            
            HistoryService.log_action(
                "create", "Invoice", invoice_number, 
                f"Generated invoice {invoice_number} for {net_amount}", user_id
            )
            
            payment_data = None
            if paid_amount > 0:
                from services.payment_service import PaymentService
                payment_data = PaymentService.create_payment(
                    company_id=company_id,
                    customer_id=customer_id,
                    amount=paid_amount,
                    payment_method=payment_method,
                    payment_date=issue_date,
                    reference_number="",
                    notes=notes,
                    invoice_id=inv.id,
                    user_id=user_id,
                    is_advance=True
                )
            
            result = {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "net_amount": float(inv.net_amount)
            }
            if payment_data:
                result["payment"] = payment_data
                
            return result

    @staticmethod
    def get_invoice_by_id(inv_id: int) -> Dict[str, Any]:
        with SessionLocal() as s:
            inv = s.query(Invoice).filter(Invoice.id == inv_id).first()
            if not inv:
                return {}
                
            from sqlalchemy import func
            from models.payment import Payment
            
            # Dynamically calculate actual paid amount to guarantee accuracy
            actual_paid = s.query(func.sum(Payment.amount)).filter(
                Payment.invoice_id == inv_id, 
                Payment.is_deleted == False
            ).scalar()
            actual_paid = float(actual_paid) if actual_paid else 0.0
            
            # Auto-sync invoice if out of sync
            if float(inv.paid_amount) != actual_paid:
                inv.paid_amount = actual_paid
                if actual_paid >= float(inv.net_amount):
                    inv.status = 'paid'
                elif actual_paid > 0:
                    inv.status = 'partial'
                else:
                    inv.status = 'unpaid'
                s.commit()
                
            items = []
            for it in inv.items:
                items.append({
                    "id": it.id,
                    "service_id": it.service_id,
                    "description": it.description,
                    "quantity": float(it.quantity),
                    "unit_price": float(it.unit_price),
                    "total_price": float(it.total_price)
                })
                
            return {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "company_id": inv.company_id,
                "customer_id": inv.customer_id,
                "customer_name": inv.customer.name if inv.customer else "",
                "issue_date": inv.issue_date,
                "total_amount": float(inv.total_amount),
                "discount": float(inv.discount),
                "tax_percentage": float(inv.tax_percentage),
                "tax_amount": float(inv.tax_amount),
                "net_amount": float(inv.net_amount),
                "paid_amount": float(inv.paid_amount),
                "status": inv.status,
                "notes": inv.notes,
                "items": items
            }

    @staticmethod
    def update_invoice(
        inv_id: int,
        customer_id: int,
        items: List[Dict[str, Any]], 
        discount: float,
        tax_percentage: float,
        notes: str,
        user_id: int
    ) -> bool:
        with SessionLocal() as s:
            inv = s.query(Invoice).filter(Invoice.id == inv_id).first()
            if not inv:
                return False
                
            # Clear old items
            s.query(InvoiceItem).filter(InvoiceItem.invoice_id == inv_id).delete()
            
            # Recalculate
            total_amount = sum(item["quantity"] * item["unit_price"] for item in items)
            tax_amount = (total_amount - discount) * (tax_percentage / 100.0)
            net_amount = (total_amount - discount) + tax_amount
            
            # Re-evaluate status based on existing paid_amount
            paid = float(inv.paid_amount)
            if paid >= net_amount:
                status = "paid"
            elif paid > 0:
                status = "partial"
            else:
                status = "unpaid"
                
            # Update fields
            inv.customer_id = customer_id
            inv.total_amount = total_amount
            inv.discount = discount
            inv.tax_percentage = tax_percentage
            inv.tax_amount = tax_amount
            inv.net_amount = net_amount
            inv.status = status
            inv.notes = notes
            
            # Insert new items
            for item in items:
                inv_item = InvoiceItem(
                    invoice_id=inv.id,
                    service_id=item["service_id"],
                    description=item["description"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    total_price=item["quantity"] * item["unit_price"]
                )
                s.add(inv_item)
                
            s.commit()
            
            HistoryService.log_action(
                "update", "Invoice", inv.invoice_number, 
                f"Updated invoice {inv.invoice_number} (New Net: {net_amount})", user_id
            )
            return True
