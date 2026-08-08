from database.session import SessionLocal
from models.history import HistoryLog
from utils.logger import logger

class HistoryService:
    """Service to handle centralized application history logging."""
    
    @staticmethod
    def log_action(action: str, entity_type: str, entity_id: str, details: str = None, user_id: int = None) -> bool:
        """
        Logs an action into the history table.
        action: 'create', 'update', 'delete', 'import', etc.
        entity_type: 'Customer', 'Invoice', etc.
        entity_id: The ID or string representation of the affected entity.
        details: Optional JSON string or text explaining the change.
        """
        try:
            with SessionLocal() as s:
                log_entry = HistoryLog(
                    action=action,
                    entity_type=entity_type,
                    entity_id=str(entity_id),
                    details=details,
                    user_id=user_id
                )
                s.add(log_entry)
                s.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to log history action: {e}")
            return False
