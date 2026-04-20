from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    DB_PATH = os.environ.get("DB_PATH", "construction_bpm_mdm.db")
    engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
