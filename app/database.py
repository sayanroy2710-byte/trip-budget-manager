import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default to SQLite database stored locally, or PostgreSQL if DATABASE_URL is set in environment (e.g. Render / Railway)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tripbudget.db")

# Fix for Render / Heroku Postgres URLs which start with 'postgres://' instead of 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables on startup if they don't exist."""
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
