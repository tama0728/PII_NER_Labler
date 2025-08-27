"""
Database initialization and management
Centralized database instance for the application
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base class for all database models"""
    pass

# Global database instance
db = SQLAlchemy(model_class=Base)