from database.session import SessionLocal
from models.expense import Expense
from models.employee_advance import EmployeeAdvance
from services.history import HistoryService

def add_methods_to_service():
    code = '''
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
'''
    with open(r'd:\Account_System\services\daybook_service.py', 'a', encoding='utf-8') as f:
        f.write('\n' + code)

if __name__ == '__main__':
    add_methods_to_service()
    print('done')
