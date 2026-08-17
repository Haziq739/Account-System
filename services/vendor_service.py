import csv
from typing import List, Tuple
from sqlalchemy import or_
from database.session import SessionLocal
from models.vendor import Vendor
from services.history import HistoryService
from utils.logger import logger

class VendorService:
    """Service layer for Vendor Management."""

    @staticmethod
    def get_vendors(company_id: int, search_term: str = "") -> List[dict]:
        """Fetch all active vendors for a specific company, optionally filtered by search term."""
        with SessionLocal() as s:
            query = s.query(Vendor).filter(
                Vendor.company_id == company_id,
                Vendor.is_deleted == False
            )
            
            if search_term:
                term = f"%{search_term}%"
                query = query.filter(
                    or_(
                        Vendor.name.ilike(term),
                        Vendor.phone.ilike(term)
                    )
                )
                
            query = query.order_by(Vendor.id.asc())
            
            results = []
            for v in query.all():
                results.append({
                    "id": v.id,
                    "name": v.name,
                    "phone": v.phone or "",
                    "address": v.address or "",
                    "created_at": v.created_at
                })
            return results

    @staticmethod
    def create_vendor(company_id: int, name: str, phone: str, address: str, user_id: int = None) -> dict:
        """Creates a new vendor. Raises ValueError if duplicate name or phone exists within the company."""
        from sqlalchemy import func
        with SessionLocal() as s:
            # Check duplicates among active vendors in the SAME company
            conditions = [func.lower(Vendor.name) == name.lower()]
            if phone:
                conditions.append(Vendor.phone == phone)
                
            existing = s.query(Vendor).filter(
                Vendor.company_id == company_id,
                Vendor.is_deleted == False,
                or_(*conditions)
            ).first()
            
            if existing:
                raise ValueError("Duplicates found")

            new_v = Vendor(
                company_id=company_id,
                name=name,
                phone=phone,
                address=address
            )
            s.add(new_v)
            s.commit()
            
            # Log history
            HistoryService.log_action("create", "Vendor", new_v.id, f"Created vendor {name}", user_id)
            
            return {
                "id": new_v.id,
                "name": new_v.name,
                "phone": new_v.phone,
                "address": new_v.address
            }

    @staticmethod
    def update_vendor(company_id: int, vendor_id: int, name: str, phone: str, address: str, user_id: int = None) -> bool:
        """Updates an existing active vendor within a specific company."""
        with SessionLocal() as s:
            v = s.query(Vendor).filter(Vendor.id == vendor_id, Vendor.company_id == company_id, Vendor.is_deleted == False).first()
            if not v:
                return False
                
            # Check duplicates (excluding self) in the SAME company
            from sqlalchemy import func
            conditions = [func.lower(Vendor.name) == name.lower()]
            if phone:
                conditions.append(Vendor.phone == phone)
                
            existing = s.query(Vendor).filter(
                Vendor.id != vendor_id,
                Vendor.company_id == company_id,
                Vendor.is_deleted == False,
                or_(*conditions)
            ).first()
            if existing:
                raise ValueError("Duplicates found")
                
            v.name = name
            v.phone = phone
            v.address = address
            s.commit()
            
            HistoryService.log_action("update", "Vendor", v.id, f"Updated vendor {name}", user_id)
            return True

    @staticmethod
    def soft_delete_vendor(company_id: int, vendor_id: int, user_id: int = None) -> bool:
        """Soft deletes a vendor within a specific company."""
        with SessionLocal() as s:
            v = s.query(Vendor).filter(Vendor.id == vendor_id, Vendor.company_id == company_id, Vendor.is_deleted == False).first()
            if not v:
                return False
                
            v.is_deleted = True
            name = v.name
            s.commit()
            
            HistoryService.log_action("delete", "Vendor", vendor_id, f"Soft deleted vendor {name}", user_id)
            return True

    @staticmethod
    def import_vendors_from_csv(company_id: int, file_path: str, user_id: int = None) -> Tuple[int, int, int]:
        """
        Reads CSV and imports vendors for a specific company.
        Returns tuple: (imported_count, skipped_count, failed_count)
        Expected format: Vendor Name, Phone, Address
        """
        imported = 0
        skipped = 0
        failed = 0
        
        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                # Check for required headers
                headers = [h.strip().lower() for h in reader.fieldnames or []]
                name_key = next((h for h in reader.fieldnames if h and h.strip().lower() in ['vendor name', 'name', 'vendor']), None)
                phone_key = next((h for h in reader.fieldnames if h and h.strip().lower() in ['phone number', 'phone', 'contact', 'mobile']), None)
                addr_key = next((h for h in reader.fieldnames if h and h.strip().lower() in ['address', 'location', 'city']), None)
                
                if not name_key or not phone_key:
                    logger.error(f"CSV missing columns. Found headers: {reader.fieldnames}")
                    raise ValueError("CSV must contain 'Vendor Name' and 'Phone Number' columns.")

                with SessionLocal() as s:
                    # Pre-load all active names and phones into memory for instant duplicate checking
                    active_vendors = s.query(Vendor.name, Vendor.phone).filter(Vendor.company_id == company_id, Vendor.is_deleted == False).all()
                    existing_names = {v.name.lower() for v in active_vendors if v.name}
                    existing_phones = {v.phone for v in active_vendors if v.phone}
                    
                    new_vendors = []
                    
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
                            
                        new_v = Vendor(
                            company_id=company_id,
                            name=name,
                            phone=phone,
                            address=addr
                        )
                        new_vendors.append(new_v)
                        
                        # Add to local sets to prevent duplicates within the CSV itself
                        existing_names.add(name_lower)
                        if phone:
                            existing_phones.add(phone)
                            
                        imported += 1
                        
                    if new_vendors:
                        s.add_all(new_vendors)
                        s.commit()
                        HistoryService.log_action("import", "Vendor", "Bulk", f"Imported {imported} vendors from CSV", user_id)
                        
            return imported, skipped, failed
            
        except Exception as e:
            logger.error(f"CSV Import Failed: {e}")
            raise e
