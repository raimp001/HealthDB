"""
HealthDB Database Configuration
SQLAlchemy setup for PostgreSQL (production) or SQLite (development)
"""
import os
import tempfile
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

# Why a missing DATABASE_URL is handled so carefully.
#
# This used to fall straight through to a local SQLite file. On a serverless
# deployment that is two failures at once. The filesystem is read-only, so
# `data_dir.mkdir()` raises OSError while api.database is still being
# imported — before the app object exists, before any try/except, before
# /api/health can report anything — and every route dies at the platform
# level with no cause in the response.
#
# The second failure is the one that would have been worse if the directory
# had been writable: a production API quietly serving an empty per-instance
# SQLite file in place of the real database. Each cold start gets its own.
# Patients' records would appear to vanish, and consent and access logs would
# be written somewhere nobody reads. For a platform whose promise is that a
# person can see where their data went, inventing a throwaway database is a
# worse outcome than refusing to serve.
#
# So: the convenience fallback stays for local development, and production
# without a configured database records the fact and carries on starting, so
# the health check can say what is wrong instead of the process dying.
IN_PRODUCTION = os.environ.get("ENVIRONMENT", "development") == "production"
DATABASE_CONFIG_ERROR = None

if not DATABASE_URL and IN_PRODUCTION:
    DATABASE_CONFIG_ERROR = (
        "DATABASE_URL is not set. This deployment is marked production, so no "
        "local database is substituted: serving an empty per-instance file in "
        "place of the real database would hide every record rather than report "
        "the problem."
    )
    # No engine is built at all. Handing create_engine a placeholder URL
    # loads that URL's driver immediately, which is the same import-time
    # failure in a new costume.
    DATABASE_URL = None
    is_sqlite = False
elif not DATABASE_URL:
    # Local development. Fall back to a writable location rather than assuming
    # the checkout is writable.
    try:
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
    except OSError:
        data_dir = Path(tempfile.gettempdir()) / "healthdb"
        data_dir.mkdir(exist_ok=True)
    DATABASE_URL = f"sqlite:///{data_dir}/healthdb.db"
    is_sqlite = True
else:
    is_sqlite = DATABASE_URL.startswith("sqlite:")
    # Name the PostgreSQL driver rather than letting SQLAlchemy choose.
    #
    # A bare "postgresql://" URL means "whatever the installed SQLAlchemy
    # defaults to", and that default changed: 2.0 loads psycopg2, 2.1 loads
    # psycopg (v3). This project installs psycopg2. requirements.txt floored
    # SQLAlchemy without capping it, so the first fresh build after 2.1 was
    # released imported a driver that was not there, raised
    # ModuleNotFoundError while this module was loading, and took every /api
    # route down for days — with no change to the application at all.
    #
    # Also covers the Heroku/Railway "postgres://" spelling.
    for bare in ("postgres://", "postgresql://"):
        if DATABASE_URL.startswith(bare):
            DATABASE_URL = "postgresql+psycopg2://" + DATABASE_URL[len(bare):]
            break

# Create engine with appropriate settings
if DATABASE_CONFIG_ERROR:
    # Unbound: importing works, and the first attempt to use the database
    # fails per request, where the health check can report the reason.
    engine = None
elif is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

