# src/models/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import get_settings

settings = get_settings()

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=settings.debug,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_db() -> Session:
    """Get database session dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    from src.models.entities import (
        PurchaseOrder,
        PurchaseOrderLine,
        Invoice,
        InvoiceLine,
        DeliveryNote,
        DeliveryNoteLine,
        MatchingResult,
        MatchingConfirmation,
        BalanceLedger,
        User,
    )
    Base.metadata.create_all(bind=engine)
