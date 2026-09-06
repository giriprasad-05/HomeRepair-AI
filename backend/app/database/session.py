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

def _create_and_verify_engine():
    global DATABASE_URL
    if not DATABASE_URL.startswith("sqlite"):
        try:
            test_engine = create_engine(DATABASE_URL, **engine_kwargs)
            with test_engine.connect() as conn:
                pass
            return test_engine
        except Exception:
            # Fallback gracefully to persistent SQLite database file in backend root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            sqlite_file = os.path.join(base_dir, "homerepair_ai.db")
            DATABASE_URL = f"sqlite:///{sqlite_file}"
            return create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        return create_engine(DATABASE_URL, **engine_kwargs)

engine = _create_and_verify_engine()

# Enable foreign keys for SQLite
from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if str(engine.url).startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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
