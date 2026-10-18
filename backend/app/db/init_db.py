import logging
from app.db.base import Base
from app.db.models import DocumentModel, MessageModel, ThreadModel  # ensure models are imported
from app.db.session import engine

logger = logging.getLogger(__name__)

async def init_db() -> None:
    """Initialize database tables automatically on startup."""
    logger.info("Initializing database schema...")
    async with engine.begin() as conn:
        # Auto-create all tables if they don't already exist
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")
