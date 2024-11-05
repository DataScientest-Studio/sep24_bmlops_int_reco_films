# src/models/user_model.py

from sqlalchemy import Column, Integer, String
from src.models.database import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(128), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
