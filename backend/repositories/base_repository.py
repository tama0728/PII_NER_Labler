"""
Base repository pattern implementation
Generic CRUD operations for all models
"""

from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.database import db

ModelType = TypeVar('ModelType')

class BaseRepository(Generic[ModelType]):
    """Generic repository for basic CRUD operations"""
    
    def __init__(self, model_class: Type[ModelType]):
        self.model_class = model_class
        self.session: Session = db.session
    
    def create(self, **kwargs) -> ModelType:
        """Create a new record"""
        try:
            instance = self.model_class(**kwargs)
            self.session.add(instance)
            self.session.commit()
            self.session.refresh(instance)
            return instance
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Failed to create {self.model_class.__name__}: {str(e)}")
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get record by ID"""
        return self.session.query(self.model_class).filter(self.model_class.id == id).first()
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[ModelType]:
        """Get all records with optional pagination"""
        query = self.session.query(self.model_class)
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """Update record by ID"""
        try:
            instance = self.get_by_id(id)
            if not instance:
                return None
            
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            self.session.commit()
            self.session.refresh(instance)
            return instance
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Failed to update {self.model_class.__name__}: {str(e)}")
    
    def delete(self, id: int) -> bool:
        """Delete record by ID"""
        try:
            instance = self.get_by_id(id)
            if not instance:
                return False
            
            self.session.delete(instance)
            self.session.commit()
            return True
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Failed to delete {self.model_class.__name__}: {str(e)}")
    
    def exists(self, id: int) -> bool:
        """Check if record exists"""
        return self.session.query(self.model_class.id).filter(self.model_class.id == id).first() is not None
    
    def count(self) -> int:
        """Count total records"""
        return self.session.query(self.model_class).count()
    
    def find_by(self, **filters) -> List[ModelType]:
        """Find records by arbitrary filters"""
        query = self.session.query(self.model_class)
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.filter(getattr(self.model_class, key) == value)
        return query.all()
    
    def find_first_by(self, **filters) -> Optional[ModelType]:
        """Find first record by filters"""
        results = self.find_by(**filters)
        return results[0] if results else None
    
    def bulk_create(self, records: List[Dict[str, Any]]) -> List[ModelType]:
        """Create multiple records in one transaction"""
        try:
            instances = [self.model_class(**record) for record in records]
            self.session.add_all(instances)
            self.session.commit()
            
            # Refresh all instances to get their IDs
            for instance in instances:
                self.session.refresh(instance)
            
            return instances
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Failed to bulk create {self.model_class.__name__}: {str(e)}")
    
    def bulk_delete(self, ids: List[int]) -> int:
        """Delete multiple records by IDs"""
        try:
            deleted_count = self.session.query(self.model_class)\
                                      .filter(self.model_class.id.in_(ids))\
                                      .delete(synchronize_session=False)
            self.session.commit()
            return deleted_count
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Failed to bulk delete {self.model_class.__name__}: {str(e)}")
    
    def paginate(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get paginated results"""
        offset = (page - 1) * per_page
        
        query = self.session.query(self.model_class)
        total = query.count()
        items = query.limit(per_page).offset(offset).all()
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
            'has_prev': page > 1,
            'has_next': page * per_page < total
        }