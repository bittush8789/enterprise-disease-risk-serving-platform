import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger("disease_risk_serving")

# Configure connection pooling for production-grade throughput
# 10,000+ RPM requires optimized connection pool and reuse settings
try:
    engine = create_engine(
        settings.database_url,
        pool_size=20,          # Keep up to 20 connections open in pool
        max_overflow=15,       # Allow up to 15 additional temporary connections
        pool_timeout=30,       # Wait up to 30s for a free connection
        pool_recycle=1800,     # Recycle connections older than 30 mins
        pool_pre_ping=True     # Test connection health before using it
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.error(f"Failed to initialize database engine: {e}")
    # In case settings.database_url fails, we keep a lazy fallback for tests
    engine = None
    SessionLocal = None

Base = declarative_base()

def get_db() -> Generator:
    """Dependency for acquiring a database session."""
    if SessionLocal is None:
        raise RuntimeError("Database engine is not initialized.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
