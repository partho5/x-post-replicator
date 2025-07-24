# __init__.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from ..config import config
import os

# Ensure data directory exists
os.makedirs(os.path.dirname(config.database_url.replace("sqlite:///", "")), exist_ok=True)

engine = create_engine(config.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_database():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    from .models import Base
    Base.metadata.create_all(bind=engine)