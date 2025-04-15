"""
Database session configuration.

This module sets up the SQLAlchemy engine, session factory, and Base class.
It also configures pgvector extension for vector embeddings.
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/zenplify_agent")
PGVECTOR_ENABLED = os.getenv("PGVECTOR_ENABLED", "true").lower() == "true"

# Configure logging
logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool if "pytest" in os.environ.get("PYTHONPATH", "") else None,
    echo=os.getenv("DEBUG", "false").lower() == "true",
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for models
Base = declarative_base()

# Setup pgvector extension if enabled
@event.listens_for(engine, "connect")
def setup_pgvector(dbapi_connection, connection_record):
    """Create pgvector extension if it doesn't exist."""
    if not PGVECTOR_ENABLED:
        logger.warning("pgvector extension is disabled, vector search will not work")
        return

    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cursor.close()
        dbapi_connection.commit()
        logger.info("pgvector extension enabled")
    except Exception as e:
        logger.error(f"Failed to create pgvector extension: {e}")
        # Don't raise the exception, as the application might still work without vector search

def get_db():
    """
    Database session dependency.
    
    Yields:
        Session: A SQLAlchemy session
        
    Usage:
        ```
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 