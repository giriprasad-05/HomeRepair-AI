import os
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Load environment variables from .env file if present
load_dotenv()

# Build or read database URL
def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Standardize postgres:// to postgresql:// for SQLAlchemy 1.4+ / 2.0
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return database_url

    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    server = os.getenv("POSTGRES_SERVER", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "homerepair_ai")

    return f"postgresql://{user}:{password}@{server}:{port}/{db}"


DATABASE_URL = get_database_url()

# Engine configuration
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
    })

try:
    engine = create_engine(DATABASE_URL, **engine_kwargs)
except Exception:
    # If psycopg2 / PostgreSQL driver is not yet available, fallback gracefully for schema generation & offline tooling
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# FastAPI Database Dependency
def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session scope."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
