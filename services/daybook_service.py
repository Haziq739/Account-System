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
        Combines them into a chronological list with running balance.
        """
        with SessionLocal() as s:
            from sqlalchemy.orm import joinedload
            from datetime import timedelta
            
            next_date = target_date + timedelta(days=1)
            
            # Fetch Income (Payments)
            payments = s.query(Payment).options(
                joinedload(Payment.customer),
                joinedload(Payment.invoice)
            ).filter(
                Payment.company_id == company_id,
                Payment.payment_date >= target_date,
                Payment.payment_date < next_date,
                Payment.is_deleted == False
            ).all()
            
            # Fetch Expenses
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
            
            running_balance = 0.0
            for t in transactions:
                running_balance += t["income"]
                running_balance -= t["expense"]
                t["running_balance"] = running_balance
                
            return {
                "transactions": transactions,
                "total_income": total_income,
                "total_expense": total_expense,
                "balance": total_income - total_expense
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
