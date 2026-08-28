from typing import List, Dict, Any
from database.session import SessionLocal

class LedgerService:

    @staticmethod
    def get_customer_ledger(company_id: int, customer_id: int, start_date=None, end_date=None) -> List[Dict[str, Any]]:
        with SessionLocal() as s:
            from models.invoice import Invoice
            from models.payment import Payment
            from models.expense import Expense
            from models.ledger import CustomerLedger
            from sqlalchemy import func
            
            opening_balance = 0.0
            if start_date:
                inv_sum = s.query(func.sum(Invoice.net_amount)).filter(
                    Invoice.company_id == company_id,
                    Invoice.customer_id == customer_id,
                    Invoice.is_deleted == False,
                    Invoice.issue_date < start_date
                ).scalar() or 0.0
                
                pay_sum = s.query(func.sum(Payment.amount)).filter(
                    Payment.company_id == company_id,
                    Payment.customer_id == customer_id,
                    Payment.is_deleted == False,
                    Payment.payment_date < start_date
                ).scalar() or 0.0
                
                # Customer-linked expenses that happened before start_date also reduce credit
                exp_sum = s.query(func.sum(Expense.amount)).filter(
                    Expense.company_id == company_id,
                    Expense.customer_id == customer_id,
                    Expense.is_deleted == False,
                    Expense.expense_date < start_date
                ).scalar() or 0.0
                
                adj_sum = s.query(func.sum(CustomerLedger.debit)).filter(
                    CustomerLedger.company_id == company_id,
                    CustomerLedger.customer_id == customer_id,
                    CustomerLedger.transaction_type == 'adjustment',
                    CustomerLedger.transaction_date < start_date
                ).scalar() or 0.0
                
                opening_balance = float(inv_sum) - float(pay_sum) + float(exp_sum) + float(adj_sum)
                
            inv_query = s.query(Invoice).filter(
                Invoice.company_id == company_id,
                Invoice.customer_id == customer_id,
                Invoice.is_deleted == False
            )
            pay_query = s.query(Payment).filter(
                Payment.company_id == company_id,
                Payment.customer_id == customer_id,
                Payment.is_deleted == False
            )
            exp_query = s.query(Expense).filter(
                Expense.company_id == company_id,
                Expense.customer_id == customer_id,
                Expense.is_deleted == False
            )
            adj_query = s.query(CustomerLedger).filter(
                CustomerLedger.company_id == company_id,
                CustomerLedger.customer_id == customer_id,
                CustomerLedger.transaction_type == 'adjustment'
            )
            
            if start_date:
                inv_query = inv_query.filter(Invoice.issue_date >= start_date)
                pay_query = pay_query.filter(Payment.payment_date >= start_date)
                exp_query = exp_query.filter(Expense.expense_date >= start_date)
                adj_query = adj_query.filter(CustomerLedger.transaction_date >= start_date)
            if end_date:
                inv_query = inv_query.filter(Invoice.issue_date <= end_date)
                pay_query = pay_query.filter(Payment.payment_date <= end_date)
                exp_query = exp_query.filter(Expense.expense_date <= end_date)
                adj_query = adj_query.filter(CustomerLedger.transaction_date <= end_date)
                
            invoices = inv_query.all()
            payments = pay_query.all()
            expenses = exp_query.all()
            adjustments = adj_query.all()
            
            transactions = []
            
            for inv in invoices:
                transactions.append({
                    "date": inv.issue_date,
                    "type": "invoice",
                    "ref": inv.invoice_number,
                    "desc": f"Invoice Generated: {inv.invoice_number}",
                    "debit": float(inv.net_amount),
                    "credit": 0.0,
                    "sort_key": (inv.issue_date, 1, inv.id),
                    "row_balance": float(inv.net_amount)
                })
                
            for pay in payments:
                desc_text = f"Payment Received: {pay.receipt_number}"
                if pay.invoice:
                    desc_text += f" for Invoice {pay.invoice.invoice_number}"
                else:
                    desc_text += " (Advance)"
                    
                sort_priority = 2 if getattr(pay, 'is_advance', False) else 3
                tx_type = "Advance Payment" if getattr(pay, 'is_advance', False) else "Payment"
                    
                transactions.append({
                    "date": pay.payment_date,
                    "type": tx_type,
                    "ref": pay.receipt_number,
                    "desc": desc_text,
                    "debit": 0.0,
                    "credit": float(pay.amount),
                    "sort_key": (pay.payment_date, sort_priority, pay.id),
                    "row_balance": float(pay.amount)
                })
            
            # Customer-linked Day Book expenses reduce the amount owed to customer
            for exp in expenses:
                exp_desc = f"Refund/Settlement via Expense: {exp.title}"
                if exp.notes:
                    exp_desc += f" - {exp.notes}"
                transactions.append({
                    "date": exp.expense_date,
                    "type": "Expense",
                    "ref": f"EXP-{exp.id}",
                    "desc": exp_desc,
                    "debit": float(exp.amount),  # Debit reduces credit (advance) balance
                    "credit": 0.0,
                    "sort_key": (exp.expense_date, 4, exp.id),
                    "row_balance": float(exp.amount)
                })
                
            for adj in adjustments:
                transactions.append({
                    "date": adj.transaction_date,
                    "type": "Adjustment",
                    "ref": adj.reference_id or "-",
                    "desc": adj.description or "Manual Adjustment",
                    "debit": float(adj.debit),
                    "credit": 0.0,
                    "sort_key": (adj.transaction_date, 1, adj.id),
                    "row_balance": float(adj.debit)
                })
                
            transactions.sort(key=lambda x: x["sort_key"])
            
            balance = opening_balance
            results = []
            
            if start_date and round(opening_balance, 2) != 0.00:
                results.append({
                    "id": 0,
                    "date": start_date,
                    "type": "opening balance",
                    "ref": "-",
                    "desc": "Opening Balance",
                    "debit": opening_balance if opening_balance > 0 else 0.0,
                    "credit": abs(opening_balance) if opening_balance < 0 else 0.0,
                    "balance": balance,
                    "row_balance": abs(opening_balance)
                })
            
            for idx, tx in enumerate(transactions):
                balance += tx["debit"]
                balance -= tx["credit"]
                
                # For invoices, use the specific row_balance (remaining amount). For others, use running balance.
                display_balance = tx.get("row_balance", 0.0) if tx["type"] == "invoice" else balance
                
                results.append({
                    "id": idx + 1,
                    "date": tx["date"],
                    "type": tx["type"],
                    "ref": tx["ref"],
                    "desc": tx["desc"],
                    "debit": tx["debit"],
                    "credit": tx["credit"],
                    "balance": balance,
                    "row_balance": display_balance
                })
                
            return results

    @staticmethod
    def add_adjustment(company_id: int, customer_id: int, amount: float, notes: str, date_val):
        with SessionLocal() as s:
            from models.ledger import CustomerLedger
            import time
            adj = CustomerLedger(
                company_id=company_id,
                customer_id=customer_id,
                transaction_date=date_val,
                transaction_type="adjustment",
                reference_id=f"ADJ-{int(time.time())}",
                debit=amount,
                credit=0.0,
                description=notes or "Opening Balance / Adjustment",
                balance=0.0  # Balance is calculated dynamically by get_customer_ledger
            )
            s.add(adj)
            s.commit()

