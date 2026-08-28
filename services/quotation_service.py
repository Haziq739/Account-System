from typing import List, Dict, Any
from sqlalchemy import func
from database.session import SessionLocal
from models.quotation import Quotation, QuotationItem
from models.invoice import Invoice, InvoiceItem
from services.history import HistoryService
from services.invoice_service import InvoiceService
from datetime import date, timedelta

class QuotationService:
    
    @staticmethod
    def generate_quotation_number(company_id: int) -> str:
        with SessionLocal() as s:
            from models.company import Company
            comp = s.query(Company).filter(Company.id == company_id).first()
            prefix = "Quotation-INV"
            if comp:
                if "RN Scanner" in comp.name:
                    prefix = "Quotation-RN"
                elif "K Dynamics" in comp.name:
                    prefix = "Quotation-KD"
            
            count = s.query(Quotation).filter(Quotation.company_id == company_id).count()
            seq = count + 1
            return f"{prefix}-{seq:03d}"

    @staticmethod
    def get_quotations(company_id: int, context: str = "regular") -> List[Dict[str, Any]]:
        with SessionLocal() as s:
            from sqlalchemy.orm import joinedload
            query = s.query(Quotation).options(joinedload(Quotation.customer)).filter(
                Quotation.company_id == company_id,
                Quotation.is_deleted == False
            )
            if context == "regular":
                query = query.filter(Quotation.customer.has(customer_type="regular"))
            else:
                query = query.filter(Quotation.customer.has(customer_type="day_book"))
                
            quotations = query.order_by(Quotation.id.desc()).all()
            
            results = []
            for q in quotations:
                results.append({
                    "id": q.id,
                    "quotation_number": q.quotation_number,
                    "category": q.category,
                    "customer_id": q.customer_id,
                    "customer_name": q.customer.name if q.customer else "Unknown",
                    "issue_date": q.issue_date,
                    "valid_until": q.valid_until,
                    "net_amount": float(q.net_amount),
                    "status": q.status,
                })
            return results

    @staticmethod
    def get_quotation(quotation_id: int) -> Dict[str, Any]:
        with SessionLocal() as s:
            q = s.query(Quotation).filter(Quotation.id == quotation_id, Quotation.is_deleted == False).first()
            if not q:
                return {}
            
            items = []
            for item in q.items:
                items.append({
                    "id": item.id,
                    "service_id": item.service_id,
                    "service_name": item.service.name if item.service else "",
                    "description": item.description,
                    "quantity": float(item.quantity),
                    "unit_price": float(item.unit_price),
                    "total_price": float(item.total_price)
                })
                
            return {
                "id": q.id,
                "quotation_number": q.quotation_number,
                "company_id": q.company_id,
                "customer_id": q.customer_id,
                "customer_name": q.customer.name if q.customer else "Unknown",
                "category": q.category,
                "issue_date": q.issue_date,
                "valid_until": q.valid_until,
                "total_amount": float(q.total_amount),
                "discount": float(q.discount),
                "tax_percentage": float(q.tax_percentage),
                "tax_amount": float(q.tax_amount),
                "net_amount": float(q.net_amount),
                "notes": q.notes,
                "status": q.status,
                "items": items
            }

    @staticmethod
    def create_quotation(
        company_id: int,
        customer_id: int,
        issue_date: date,
        valid_until: date,
        items: List[Dict[str, Any]], 
        discount: float,
        tax_percentage: float,
        notes: str,
        user_id: int
    ) -> Dict[str, Any]:
        
        with SessionLocal() as s:
            quotation_number = QuotationService.generate_quotation_number(company_id)
            
            # Calculate totals exactly like invoices
            total_amount = sum(item["quantity"] * item["unit_price"] for item in items)
            tax_amount = (total_amount - discount) * (tax_percentage / 100.0)
            net_amount = (total_amount - discount) + tax_amount
                
            q = Quotation(
                quotation_number=quotation_number,
                company_id=company_id,
                customer_id=customer_id,
                category="GENERAL",
                issue_date=issue_date,
                valid_until=valid_until,
                total_amount=total_amount,
                discount=discount,
                tax_percentage=tax_percentage,
                tax_amount=tax_amount,
                net_amount=net_amount,
                status="pending",
                notes=notes
            )
            s.add(q)
            s.flush() # Get ID
            
            # Add items
            for item in items:
                q_item = QuotationItem(
                    quotation_id=q.id,
                    service_id=item["service_id"],
                    description=item["description"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    total_price=item["quantity"] * item["unit_price"]
                )
                s.add(q_item)
                
            # No ledger entry for quotations
            s.commit()
            
            HistoryService.log_action(
                "create", "Quotation", quotation_number, 
                f"Generated quotation {quotation_number} for {net_amount}", user_id
            )
            
            return {"success": True, "quotation_id": q.id}

    @staticmethod
    def update_quotation(
        quotation_id: int,
        customer_id: int,
        items: List[Dict[str, Any]], 
        discount: float,
        tax_percentage: float,
        notes: str,
        user_id: int
    ) -> bool:
        with SessionLocal() as s:
            q = s.query(Quotation).filter(Quotation.id == quotation_id).first()
            if not q:
                return False
                
            # Clear old items
            s.query(QuotationItem).filter(QuotationItem.quotation_id == quotation_id).delete()
            
            # Recalculate
            total_amount = sum(item["quantity"] * item["unit_price"] for item in items)
            tax_amount = (total_amount - discount) * (tax_percentage / 100.0)
            net_amount = (total_amount - discount) + tax_amount
                
            # Update fields
            q.customer_id = customer_id
            q.total_amount = total_amount
            q.discount = discount
            q.tax_percentage = tax_percentage
            q.tax_amount = tax_amount
            q.net_amount = net_amount
            q.notes = notes
            
            # Insert new items
            for item in items:
                q_item = QuotationItem(
                    quotation_id=q.id,
                    service_id=item["service_id"],
                    description=item["description"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    total_price=item["quantity"] * item["unit_price"]
                )
                s.add(q_item)
                
            s.commit()
            
            HistoryService.log_action(
                "update", "Quotation", q.quotation_number, 
                f"Updated quotation {q.quotation_number} (New Net: {net_amount})", user_id
            )
            
            # Invalidate PDF cache
            import os
            pdf_dir = os.path.join(os.getcwd(), "quotations")
            filepath = os.path.join(pdf_dir, f"{q.quotation_number}.pdf")
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception:
                    pass
                    
            return True

    @staticmethod
    def delete_quotation(quotation_id: int, user_id: int) -> bool:
        with SessionLocal() as s:
            q = s.query(Quotation).filter(Quotation.id == quotation_id).first()
            if not q:
                return False
            q.is_deleted = True
            q_num = q.quotation_number
            s.commit()
            HistoryService.log_action("delete", "Quotation", q_num, f"Deleted quotation {q_num}", user_id)
            return True

    @staticmethod
    def convert_to_invoice(quotation_id: int, user_id: int) -> Dict[str, Any]:
        """Converts a pending quotation into a fully fledged Invoice using InvoiceService."""
        q_data = QuotationService.get_quotation(quotation_id)
        if not q_data:
            return {"success": False, "message": "Quotation not found"}
        
        if q_data["status"] == "converted":
            return {"success": False, "message": "Quotation is already converted"}
            
        # Re-pack items for InvoiceService
        items_payload = []
        for item in q_data["items"]:
            items_payload.append({
                "service_id": item["service_id"],
                "description": item["description"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"]
            })
            
        # Call the existing battle-tested InvoiceService logic
        res = InvoiceService.create_invoice(
            company_id=q_data["company_id"],
            customer_id=q_data["customer_id"],
            issue_date=date.today(),
            items=items_payload,
            discount=q_data["discount"],
            tax_percentage=q_data["tax_percentage"],
            paid_amount=0.0,
            payment_method="",
            notes=q_data["notes"] or "",
            user_id=user_id
        )
        
        if res.get("id"):
            # Mark the quotation as converted
            with SessionLocal() as s:
                q = s.query(Quotation).filter(Quotation.id == quotation_id).first()
                if q:
                    q.status = "converted"
                    s.commit()
                    HistoryService.log_action(
                        "convert", "Quotation", q.quotation_number, 
                        f"Converted quotation {q.quotation_number} to invoice", user_id
                    )
            res["success"] = True
            
            # Pack full UI-ready invoice data
            # get_quotation returns "customer_name" inside it? No, but we can fetch it or just pass "Unknown" 
            # wait, we can just fetch the created invoice using InvoiceService.get_invoices? No, it returns a list.
            # We can use InvoiceService.get_invoice_by_id!
            full_inv = InvoiceService.get_invoice_by_id(res["id"])
            if full_inv:
                res["invoice_data"] = full_inv
            
        return res
