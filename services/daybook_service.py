from datetime import date
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database.session import SessionLocal
from models.payment import Payment
from models.expense import Expense
from services.history import HistoryService

class DayBookService:
    @staticmethod
    def get_daybook_transactions(company_id: int, target_date: date) -> Dict[str, Any]:
        """
        Fetches all incomes (payments) and expenses for a given day and company.
        Combines them into a chronological list with running balance starting from the previous closing balance.
        """
        with SessionLocal() as s:
            from sqlalchemy.orm import joinedload
            from sqlalchemy import func
            from datetime import timedelta
            
            next_date = target_date + timedelta(days=1)
            
            # Calculate Opening Balance (Previous Closing Balance)
            hist_income_query = s.query(func.sum(Payment.amount)).filter(
                Payment.company_id == company_id,
                Payment.payment_date < target_date,
                Payment.is_deleted == False
            ).scalar()
            hist_income = float(hist_income_query or 0.0)
            
            hist_expense_query = s.query(func.sum(Expense.amount)).filter(
                Expense.company_id == company_id,
                Expense.expense_date < target_date,
                Expense.is_deleted == False
            ).scalar()
            hist_expense = float(hist_expense_query or 0.0)
            
            opening_balance = hist_income - hist_expense
            
            # Fetch Income (Payments) for the day
            payments = s.query(Payment).options(
                joinedload(Payment.customer),
                joinedload(Payment.invoice)
            ).filter(
                Payment.company_id == company_id,
                Payment.payment_date >= target_date,
                Payment.payment_date < next_date,
                Payment.is_deleted == False
            ).all()
            
            # Fetch Expenses for the day
            expenses = s.query(Expense).options(
                joinedload(Expense.customer),
                joinedload(Expense.vendor),
                joinedload(Expense.employee)
            ).filter(
                Expense.company_id == company_id,
                Expense.expense_date >= target_date,
                Expense.expense_date < next_date,
                Expense.is_deleted == False
            ).all()
            
            transactions = []
            total_income = 0.0
            total_expense = 0.0
            
            for p in payments:
                amount = float(p.amount)
                total_income += amount
                
                type_label = "Advance Payment" if p.is_advance else "Payment"
                desc = p.notes or f"Receipt #{p.receipt_number}"
                if p.payment_method:
                    desc += f" via {p.payment_method}"
                    
                customer_name = p.customer.name if p.customer else "Walk-in"
                invoice_num = p.invoice.invoice_number if p.invoice else ""
                
                transactions.append({
                    "id": f"pay_{p.id}",
                    "timestamp": p.created_at,
                    "type": type_label,
                    "description": desc,
                    "customer_or_title": customer_name,
                    "invoice_number": invoice_num,
                    "income": amount,
                    "expense": 0.0,
                    "sort_key": p.created_at.timestamp() if p.created_at else 0
                })
                
            for e in expenses:
                amount = float(e.amount)
                total_expense += amount
                
                entity_name = ""
                if e.vendor:
                    entity_name = e.vendor.name
                elif e.customer:
                    entity_name = e.customer.name
                elif e.employee:
                    entity_name = e.employee.name
                
                transactions.append({
                    "id": f"exp_{e.id}",
                    "timestamp": e.created_at,
                    "type": "Expense",
                    "description": f"{e.title} - {e.notes}" if e.notes else e.title,
                    "customer_or_title": entity_name,
                    "invoice_number": "",
                    "income": 0.0,
                    "expense": amount,
                    "sort_key": e.created_at.timestamp() if e.created_at else 0
                })
                
            # Sort chronologically
            transactions.sort(key=lambda x: x["sort_key"])
            
            running_balance = opening_balance
            for t in transactions:
                running_balance += t["income"]
                running_balance -= t["expense"]
                t["running_balance"] = running_balance
                
            closing_balance = opening_balance + total_income - total_expense
                
            return {
                "transactions": transactions,
                "opening_balance": opening_balance,
                "total_income": total_income,
                "total_expense": total_expense,
                "balance": closing_balance
            }

    @staticmethod
    def add_expense(company_id: int, title: str, amount: float, expense_date: date, notes: str, user_id: int = None, customer_id: int = None, vendor_id: int = None, employee_id: int = None) -> dict:
        """Adds a manual expense entry for the Day Book."""
        from models.employee_advance import EmployeeAdvance
        with SessionLocal() as s:
            new_exp = Expense(
                company_id=company_id,
                title=title,
                amount=amount,
                expense_date=expense_date,
                notes=notes,
                customer_id=customer_id,
                vendor_id=vendor_id,
                employee_id=employee_id
            )
            s.add(new_exp)
            s.flush() # to get new_exp.id
            
            if employee_id:
                month_str = expense_date.strftime("%B %Y")
                new_adv = EmployeeAdvance(
                    company_id=company_id,
                    employee_id=employee_id,
                    expense_id=new_exp.id,
                    amount=amount,
                    advance_date=expense_date,
                    month=month_str,
                    description=f"{title} - {notes}" if notes else title
                )
                s.add(new_adv)
                
            s.commit()
            
            HistoryService.log_action("create", "Expense", new_exp.id, f"Added expense '{title}' for {amount}", user_id)
            
            return {
                "id": new_exp.id,
                "title": new_exp.title,
                "amount": float(new_exp.amount)
            }


    @staticmethod
    def get_expense(expense_id: int) -> dict:
        with SessionLocal() as s:
            e = s.query(Expense).filter(Expense.id == expense_id).first()
            if not e: return None
            return {
                "id": e.id,
                "title": e.title,
                "amount": float(e.amount),
                "expense_date": e.expense_date,
                "notes": e.notes or "",
                "customer_id": e.customer_id,
                "vendor_id": e.vendor_id,
                "employee_id": e.employee_id
            }

    @staticmethod
    def update_expense(expense_id: int, title: str, amount: float, expense_date, notes: str, user_id: int = None, customer_id: int = None, vendor_id: int = None, employee_id: int = None):
        from models.employee_advance import EmployeeAdvance
        with SessionLocal() as s:
            e = s.query(Expense).filter(Expense.id == expense_id).first()
            if not e: raise Exception("Expense not found")
            
            e.title = title
            e.amount = amount
            e.expense_date = expense_date
            e.notes = notes
            e.customer_id = customer_id
            e.vendor_id = vendor_id
            e.employee_id = employee_id
            
            adv = s.query(EmployeeAdvance).filter(EmployeeAdvance.expense_id == expense_id).first()
            if employee_id:
                month_str = expense_date.strftime("%B %Y")
                if adv:
                    adv.employee_id = employee_id
                    adv.amount = amount
                    adv.advance_date = expense_date
                    adv.month = month_str
                    adv.description = f"{title} - {notes}" if notes else title
                else:
                    new_adv = EmployeeAdvance(
                        company_id=e.company_id,
                        employee_id=employee_id,
                        expense_id=e.id,
                        amount=amount,
                        advance_date=expense_date,
                        month=month_str,
                        description=f"{title} - {notes}" if notes else title
                    )
                    s.add(new_adv)
            else:
                if adv:
                    s.delete(adv)
                    
            s.commit()
            HistoryService.log_action("update", "Expense", e.id, f"Updated expense '{title}' to {amount}", user_id)
            return True
