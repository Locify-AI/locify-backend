from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from sqlalchemy.pool import NullPool

# SQLite database file path
SQLALCHEMY_DATABASE_URL = "sqlite:///./locify.db"

USE_NULL_POOL = os.getenv("SQLITE_NULL_POOL", "1") == "1"

# For SQLite under concurrent async tasks (e.g., narration generation), a QueuePool can overflow.
# Using NullPool avoids holding connections open; each session gets a fresh connection.
if USE_NULL_POOL:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
        echo=False,
        future=True,
    )
else:
    # Tuned pool settings if later switching to a different DB (Postgres/MySQL) or keeping pool.
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),
        future=True,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

