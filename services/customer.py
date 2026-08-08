import csv
import io
from typing import List, Dict, Tuple
from sqlalchemy import or_
from database.session import SessionLocal
from models.customer import Customer
from services.history import HistoryService
from utils.logger import logger

class CustomerService:
    """Service layer for Customer Management."""

    @staticmethod
    def get_customers(search_term: str = "", customer_type: str = "regular") -> List[dict]:
        """Fetch all active customers, optionally filtered by search term and type."""
        with SessionLocal() as s:
            query = s.query(Customer).filter(
                Customer.is_deleted == False,
                Customer.customer_type == customer_type
            )
            
            if search_term:
                term = f"%{search_term}%"
                query = query.filter(
                    or_(
                        Customer.name.ilike(term),
                        Customer.phone.ilike(term)
                    )
                )
                
            query = query.order_by(Customer.id.asc())
            
            results = []
            for c in query.all():
                results.append({
                    "id": c.id,
                    "name": c.name,
                    "phone": c.phone or "",
                    "address": c.address or "",
                    "created_at": c.created_at
                })
            return results

    @staticmethod
    def get_customers_with_ledger(company_id: int, customer_type: str = "regular") -> List[dict]:
        """Fetch active customers that have transactions for a specific company."""
        with SessionLocal() as s:
            from models.invoice import Invoice
            from models.payment import Payment
            
            inv_customers = s.query(Invoice.customer_id).filter(
                Invoice.company_id == company_id,
                Invoice.is_deleted == False
            ).distinct()
            
            pay_customers = s.query(Payment.customer_id).filter(
                Payment.company_id == company_id,
                Payment.is_deleted == False
            ).distinct()
            
            customer_ids = {c[0] for c in inv_customers}.union({c[0] for c in pay_customers})
            
            if not customer_ids:
                return []
                
            query = s.query(Customer).filter(
                Customer.id.in_(customer_ids),
                Customer.is_deleted == False,
                Customer.customer_type == customer_type
            ).order_by(Customer.name.asc())
            
            results = []
            for c in query.all():
                results.append({
                    "id": c.id,
                    "name": c.name,
                    "phone": c.phone or "",
                    "address": c.address or "",
                    "created_at": c.created_at
                })
            return results

    @staticmethod
    def create_customer(name: str, phone: str, address: str, user_id: int = None, customer_type: str = "regular") -> dict:
        """Creates a new customer. Raises ValueError if duplicate name or phone exists."""
        with SessionLocal() as s:
            # Check duplicates among active customers
            existing = s.query(Customer).filter(
                Customer.is_deleted == False,
                or_(
                    Customer.name == name,
                    Customer.phone == phone
                )
            ).first()
            
            if existing:
                raise ValueError("A customer with this name or phone already exists.")

            new_c = Customer(
                name=name,
                phone=phone,
                address=address,
                customer_type=customer_type
            )
            s.add(new_c)
            s.commit()
            
            # Log history
            HistoryService.log_action("create", "Customer", new_c.id, f"Created customer {name}", user_id)
            
            return {
                "id": new_c.id,
                "name": new_c.name,
                "phone": new_c.phone,
                "address": new_c.address
            }

    @staticmethod
    def update_customer(customer_id: int, name: str, phone: str, address: str, user_id: int = None) -> bool:
        """Updates an existing active customer."""
        with SessionLocal() as s:
            c = s.query(Customer).filter(Customer.id == customer_id, Customer.is_deleted == False).first()
            if not c:
                return False
                
            # Check duplicates (excluding self)
            existing = s.query(Customer).filter(
                Customer.id != customer_id,
                Customer.is_deleted == False,
                or_(
                    Customer.name == name,
                    Customer.phone == phone
                )
            ).first()
            if existing:
                raise ValueError("Another customer with this name or phone already exists.")
                
            c.name = name
            c.phone = phone
            c.address = address
            s.commit()
            
            HistoryService.log_action("update", "Customer", c.id, f"Updated customer {name}", user_id)
            return True

    @staticmethod
    def soft_delete_customer(customer_id: int, user_id: int = None) -> bool:
        """Soft deletes a customer."""
        with SessionLocal() as s:
            c = s.query(Customer).filter(Customer.id == customer_id, Customer.is_deleted == False).first()
            if not c:
                return False
                
            c.is_deleted = True
            name = c.name
            s.commit()
            
            HistoryService.log_action("delete", "Customer", customer_id, f"Soft deleted customer {name}", user_id)
            return True

    @staticmethod
    def import_customers_from_csv(file_path: str, user_id: int = None, customer_type: str = "regular") -> Tuple[int, int, int]:
        """
        Reads CSV and imports customers.
        Returns tuple: (imported_count, skipped_count, failed_count)
        Expected format: Customer Name, Phone Number, Address
        """
        imported = 0
        skipped = 0
        failed = 0
        
        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                # Check for required headers
                headers = [h.strip().lower() for h in reader.fieldnames or []]
                name_key = next((h for h in reader.fieldnames if h and h.strip().lower() in ['customer name', 'name']), None)
                phone_key = next((h for h in reader.fieldnames if h and h.strip().lower() in ['phone number', 'phone', 'contact', 'mobile']), None)
                addr_key = next((h for h in reader.fieldnames if h and h.strip().lower() in ['address', 'location', 'city']), None)
                
                if not name_key or not phone_key:
                    logger.error(f"CSV missing columns. Found headers: {reader.fieldnames}")
                    raise ValueError("CSV must contain 'Customer Name' and 'Phone Number' columns.")

                with SessionLocal() as s:
                    # Pre-load all active names and phones into memory for instant duplicate checking
                    active_custs = s.query(Customer.name, Customer.phone).filter(Customer.is_deleted == False).all()
                    existing_names = {c.name.lower() for c in active_custs if c.name}
                    existing_phones = {c.phone for c in active_custs if c.phone}
                    
                    new_customers = []
                    
                    for row_idx, row in enumerate(reader, start=2):
                        # safely handle None
                        name = str(row.get(name_key) or "").strip()
                        phone = str(row.get(phone_key) or "").strip()
                        addr = str(row.get(addr_key) or "").strip() if addr_key else ""
                        
                        # Check if row is completely empty (all fields empty)
                        is_empty_row = all(not str(val).strip() for val in row.values() if val)
                        if is_empty_row:
                            continue # silently skip blank trailing rows
                            
                        if not name:
                            if failed < 5:
                                logger.warning(f"Row {row_idx} failed validation. Name: '{name}', Phone: '{phone}', Raw Row: {row}")
                            failed += 1
                            continue
                            
                        # Check duplicate instantly via memory
                        name_lower = name.lower()
                        if name_lower in existing_names or (phone and phone in existing_phones):
                            skipped += 1
                            continue
                            
                        new_c = Customer(
                            name=name,
                            phone=phone,
                            address=addr,
                            customer_type=customer_type
                        )
                        new_customers.append(new_c)
                        
                        # Add to local sets to prevent duplicates within the CSV itself
                        existing_names.add(name_lower)
                        if phone:
                            existing_phones.add(phone)
                            
                        imported += 1
                        
                    if new_customers:
                        s.add_all(new_customers)
                        s.commit()
                        HistoryService.log_action("import", "Customer", "Bulk", f"Imported {imported} customers from CSV", user_id)
                        
            return imported, skipped, failed
            
        except Exception as e:
            logger.error(f"CSV Import Failed: {e}")
            raise e
