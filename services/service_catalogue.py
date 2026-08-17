from sqlalchemy import or_
from database.session import SessionLocal
from models.service import Service
from services.history import HistoryService

class ServiceCatalogue:
    """Service to handle Service Catalogue CRUD operations."""
    
    @staticmethod
    def get_services(company_id: int, search_term: str = "") -> list[dict]:
        with SessionLocal() as s:
            query = s.query(Service).filter(Service.company_id == company_id, Service.is_deleted == False)
            
            if search_term:
                term = f"%{search_term}%"
                query = query.filter(
                    or_(
                        Service.name.ilike(term),
                        Service.category.ilike(term)
                    )
                )
                
            query = query.order_by(Service.id.asc())
            
            results = []
            for srv in query.all():
                results.append({
                    "id": srv.id,
                    "category": srv.category,
                    "name": srv.name,
                    "description": srv.description or "",
                    "price": float(srv.default_price) if srv.default_price else 0.0,
                    "created_at": srv.created_at
                })
            return results

    @staticmethod
    def create_service(company_id: int, category: str, name: str, description: str, price: float, user_id: int) -> dict:
        with SessionLocal() as s:
            existing = s.query(Service).filter(
                Service.company_id == company_id,
                Service.name == name,
                Service.is_deleted == False
            ).first()
            
            if existing:
                raise ValueError("A service with this name already exists in this company.")
                
            srv = Service(
                company_id=company_id,
                category=category,
                name=name,
                description=description,
                default_price=price
            )
            s.add(srv)
            s.commit()
            s.refresh(srv)
            
            HistoryService.log_action("create", "Service", str(srv.id), f"Created service '{name}' in category '{category}'", user_id)
            
            return {
                "id": srv.id,
                "category": srv.category,
                "name": srv.name,
                "description": srv.description or "",
                "price": float(srv.default_price) if srv.default_price else 0.0,
                "created_at": srv.created_at
            }

    @staticmethod
    def update_service(service_id: int, category: str, name: str, description: str, price: float, user_id: int) -> bool:
        with SessionLocal() as s:
            srv = s.query(Service).filter(Service.id == service_id).first()
            if not srv or srv.is_deleted:
                return False
                
            # Check for name collisions within the same company
            existing = s.query(Service).filter(
                Service.company_id == srv.company_id,
                Service.name == name,
                Service.id != service_id,
                Service.is_deleted == False
            ).first()
            if existing:
                raise ValueError("Another service with this name already exists in this company.")
                
            changes = []
            if srv.category != category: changes.append(f"Category: {srv.category} -> {category}")
            if srv.name != name: changes.append(f"Name: {srv.name} -> {name}")
            
            old_price = float(srv.default_price) if srv.default_price else 0.0
            if old_price != price: changes.append(f"Price: {old_price} -> {price}")
            
            srv.category = category
            srv.name = name
            srv.description = description
            srv.default_price = price
            
            s.commit()
            
            if changes:
                HistoryService.log_action("update", "Service", str(srv.id), " | ".join(changes), user_id)
                
            return True

    @staticmethod
    def soft_delete_service(service_id: int, user_id: int) -> bool:
        with SessionLocal() as s:
            srv = s.query(Service).filter(Service.id == service_id).first()
            if not srv or srv.is_deleted:
                return False
                
            srv.is_deleted = True
            name = srv.name
            s.commit()
            
            HistoryService.log_action("delete", "Service", str(srv.id), f"Deleted service '{name}'", user_id)
            return True
