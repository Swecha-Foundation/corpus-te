# app/models/role.py
from sqlalchemy import Column, Integer, String
from app.db.base_class import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, index=True, nullable=False) # e.g., "admin", "user"
    description = Column(String(255), nullable=True)
