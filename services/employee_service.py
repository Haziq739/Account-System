import csv
from typing import List, Tuple
from sqlalchemy import or_
from database.session import SessionLocal
from models.employee import Employee
from services.history import HistoryService
from utils.logger import logger

class EmployeeService:
    """Service layer for Employee Management."""

    @staticmethod
    def get_employees(company_id: int, search_term: str = "") -> List[dict]:
        """Fetch all active employees for a specific company, optionally filtered by search term."""
        from sqlalchemy.orm import joinedload
        from datetime import datetime
        current_month_str = datetime.now().strftime("%B %Y")
        
        with SessionLocal() as s:
            query = s.query(Employee).options(joinedload(Employee.advances)).filter(
                Employee.company_id == company_id,
                Employee.is_deleted == False
            )
            
            if search_term:
                term = f"%{search_term}%"
                query = query.filter(
                    or_(
                        Employee.name.ilike(term),
                        Employee.phone.ilike(term)
                    )
                )
                
            query = query.order_by(Employee.id.asc())
            
            results = []
            for e in query.all():
                current_adv = sum(float(adv.amount) for adv in e.advances if not adv.is_cleared and adv.month == current_month_str)
                salary = float(e.salary) if e.salary else 0.0
                
                results.append({
                    "id": e.id,
                    "name": e.name,
                    "salary": salary,
                    "current_advance": current_adv,
                    "net_salary": salary - current_adv,
                    "phone": e.phone or "",
                    "address": e.address or "",
                    "created_at": e.created_at
                })
            return results

    @staticmethod
    def create_employee(company_id: int, name: str, salary: float, phone: str = "", address: str = "", user_id: int = None) -> dict:
        """Creates a new employee."""
        with SessionLocal() as s:
            new_e = Employee(
                company_id=company_id,
                name=name,
                salary=salary,
                phone=phone,
                address=address
            )
            s.add(new_e)
            s.commit()
            
            # Log history
            HistoryService.log_action("create", "Employee", new_e.id, f"Created employee {name} with salary {salary}", user_id)
            
            return {
                "id": new_e.id,
                "name": new_e.name,
                "salary": float(new_e.salary),
                "phone": new_e.phone,
                "address": new_e.address
            }

    @staticmethod
    def update_employee(company_id: int, employee_id: int, name: str, salary: float, phone: str = "", address: str = "", user_id: int = None) -> bool:
        """Updates an existing active employee within a specific company."""
        with SessionLocal() as s:
            e = s.query(Employee).filter(Employee.id == employee_id, Employee.company_id == company_id, Employee.is_deleted == False).first()
            if not e:
                return False
                
            e.name = name
            e.salary = salary
            e.phone = phone
            e.address = address
            s.commit()
            
            HistoryService.log_action("update", "Employee", e.id, f"Updated employee {name}", user_id)
            return True

    @staticmethod
    def soft_delete_employee(company_id: int, employee_id: int, user_id: int = None) -> bool:
        """Soft deletes an employee within a specific company."""
        with SessionLocal() as s:
            e = s.query(Employee).filter(Employee.id == employee_id, Employee.company_id == company_id, Employee.is_deleted == False).first()
            if not e:
                return False
                
            e.is_deleted = True
            name = e.name
            s.commit()
            
            HistoryService.log_action("delete", "Employee", employee_id, f"Soft deleted employee {name}", user_id)
            return True

    @staticmethod
    def clear_employee_advances(company_id: int, month_str: str, user_id: int = None) -> bool:
        """Clears (soft deletes/marks as cleared) all advances for a given month in a company."""
        from models.employee_advance import EmployeeAdvance
        with SessionLocal() as s:
            advances = s.query(EmployeeAdvance).filter(
                EmployeeAdvance.company_id == company_id,
                EmployeeAdvance.month == month_str,
                EmployeeAdvance.is_cleared == False
            ).all()
            
            for adv in advances:
                adv.is_cleared = True
                
            s.commit()
            HistoryService.log_action("update", "EmployeeAdvance", "Bulk", f"Cleared advances for month {month_str}", user_id)
            return True
            
    @staticmethod
    def get_employee_advance_history(employee_id: int) -> List[dict]:
        """Fetch all advances (cleared or not) for an employee to show in history."""
        from models.employee_advance import EmployeeAdvance
        with SessionLocal() as s:
            advances = s.query(EmployeeAdvance).filter(
                EmployeeAdvance.employee_id == employee_id
            ).order_by(EmployeeAdvance.advance_date.desc()).all()
            
            results = []
            for adv in advances:
                results.append({
                    "id": adv.id,
                    "date": adv.advance_date.strftime("%d-%b-%Y"),
                    "month": adv.month,
                    "amount": float(adv.amount),
                    "description": adv.description or "Salary Advance",
                    "is_cleared": adv.is_cleared
                })
            return results
