"""
HealthDB Database Seeder
Populate database with initial institutional partners (verified only)
"""
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Institution


def seed_institutions(db: Session) -> None:
    """Seed verified partner institutions only"""
    # Note: Only add institutions that are confirmed partners
    # Currently empty - institutions will be added as partnerships are formed
    pass


def run_seed():
    """Run all seeders"""
    db = SessionLocal()
    try:
        print("Running database initialization...")
        seed_institutions(db)
        print("Database initialization complete!")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
