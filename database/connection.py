from sqlalchemy import create_engine
from config.settings import DATABASE_URL
from utils.logger import logger

def get_engine():
    """Create and return the SQLAlchemy engine."""
    logger.info(f"Connecting to database at {DATABASE_URL}")
    # SQLite specific configuration:
    # check_same_thread=False is needed if sharing the connection across threads
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False  # Set to True to see all SQL queries in the console
    )
    return engine

# Global engine instance
engine = get_engine()
