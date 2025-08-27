"""
User repository implementation
Specialized data access for user management
"""

from typing import List, Optional
from backend.models.user import User
from backend.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    """Repository for user-specific database operations"""
    
    def __init__(self):
        super().__init__(User)
    
    def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        return self.session.query(User).filter(User.username == username).first()
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        return self.session.query(User).filter(User.email == email).first()
    
    def create_user(self, username: str, email: str, password: str, 
                   full_name: str = None, role: str = 'annotator') -> User:
        """Create a new user with password hashing"""
        # Check for existing username or email
        if self.find_by_username(username):
            raise ValueError(f"Username '{username}' already exists")
        if self.find_by_email(email):
            raise ValueError(f"Email '{email}' already exists")
        
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=role
        )
        user.set_password(password)
        
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user by username/password"""
        user = self.find_by_username(username)
        if user and user.check_password(password) and user.is_active:
            user.update_last_login()
            return user
        return None
    
    def get_active_users(self) -> List[User]:
        """Get all active users"""
        return self.session.query(User).filter(User.is_active == True).all()
    
    def get_users_by_role(self, role: str) -> List[User]:
        """Get users by role"""
        return self.session.query(User).filter(User.role == role, User.is_active == True).all()
    
    def get_admins(self) -> List[User]:
        """Get all admin users"""
        return self.get_users_by_role('admin')
    
    def get_annotators(self) -> List[User]:
        """Get all annotator users"""
        return self.get_users_by_role('annotator')
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user"""
        user = self.get_by_id(user_id)
        if user:
            user.is_active = False
            self.session.commit()
            return True
        return False
    
    def activate_user(self, user_id: int) -> bool:
        """Activate a user"""
        user = self.get_by_id(user_id)
        if user:
            user.is_active = True
            self.session.commit()
            return True
        return False
    
    def change_password(self, user_id: int, new_password: str) -> bool:
        """Change user password"""
        user = self.get_by_id(user_id)
        if user:
            user.set_password(new_password)
            self.session.commit()
            return True
        return False
    
    def change_role(self, user_id: int, new_role: str) -> bool:
        """Change user role"""
        if new_role not in ['admin', 'annotator', 'viewer']:
            raise ValueError(f"Invalid role: {new_role}")
        
        user = self.get_by_id(user_id)
        if user:
            user.role = new_role
            self.session.commit()
            return True
        return False
    
    def get_user_statistics(self, user_id: int) -> dict:
        """Get statistics for a specific user"""
        user = self.get_by_id(user_id)
        if not user:
            return {}
        
        # Import here to avoid circular imports
        from backend.models.task import Task
        from backend.models.annotation import Annotation
        
        completed_tasks = self.session.query(Task).filter(
            Task.annotator_id == user_id,
            Task.is_completed == True
        ).count()
        
        total_annotations = 0
        for task in user.tasks:
            total_annotations += len(task.annotations)
        
        return {
            'user_id': user_id,
            'username': user.username,
            'total_tasks': len(user.tasks),
            'completed_tasks': completed_tasks,
            'completion_rate': completed_tasks / len(user.tasks) * 100 if user.tasks else 0,
            'total_annotations': total_annotations,
            'projects_count': len(user.projects) if hasattr(user, 'projects') else 0
        }