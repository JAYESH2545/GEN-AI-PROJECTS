from collections.abc import Generator
from sqlalchemy.orm import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import get_Settings

Settings = get_Settings()

connect_args = {"check_same_thread": False} if Settings.database_url.startswith("sqlite") else {}

engine = create_engine(Settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) 

def get_db()-> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()