import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from src.models.database import Base
from dotenv import load_dotenv

load_dotenv()

def init_database():
    """Initialize the database with all required tables"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    engine = create_engine(DATABASE_URL)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session factory
    Session = sessionmaker(bind=engine)
    return Session()

if __name__ == "__main__":
    init_database() 