"""
User service layer
Business logic for user management and authentication
"""

from typing import Optional, List, Dict, Any
from backend.models.user import User
from backend.repositories.user_repository import UserRepository
from backend.database import db

class UserService:
    """Service for user management and authentication"""
    
    def __init__(self):
        self.user_repository = UserRepository()
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials"""
        return self.user_repository.authenticate_user(username, password)
    
    def create_user(self, username: str, email: str, password: str,
                   full_name: str = None, role: str = 'annotator') -> User:
        """Create a new user with validation"""
        # Validate input
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        if not email or '@' not in email:
            raise ValueError("Invalid email address")
        
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        if role not in ['admin', 'annotator', 'viewer']:
            raise ValueError(f"Invalid role: {role}")
        
        return self.user_repository.create_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role=role
        )
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.user_repository.get_by_id(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.user_repository.find_by_username(username)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.user_repository.find_by_email(email)
    
    def update_user_profile(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user profile information"""
        allowed_fields = ['full_name', 'email']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        # Validate email if provided
        if 'email' in update_data and '@' not in update_data['email']:
            raise ValueError("Invalid email address")
        
        return self.user_repository.update(user_id, **update_data)
    
    def change_user_password(self, user_id: int, current_password: str, 
                           new_password: str) -> bool:
        """Change user password with current password verification"""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return False
        
        # Verify current password
        if not user.check_password(current_password):
            raise ValueError("Current password is incorrect")
        
        # Validate new password
        if not new_password or len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters long")
        
        return self.user_repository.change_password(user_id, new_password)
    
    def admin_change_password(self, admin_id: int, user_id: int, 
                            new_password: str) -> bool:
        """Admin changes user password (no current password required)"""
        admin = self.user_repository.get_by_id(admin_id)
        if not admin or not admin.is_admin():
            raise ValueError("Only admin users can change other users' passwords")
        
        if not new_password or len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters long")
        
        return self.user_repository.change_password(user_id, new_password)
    
    def change_user_role(self, admin_id: int, user_id: int, new_role: str) -> bool:
        """Change user role (admin only)"""
        admin = self.user_repository.get_by_id(admin_id)
        if not admin or not admin.is_admin():
            raise ValueError("Only admin users can change user roles")
        
        return self.user_repository.change_role(user_id, new_role)
    
    def deactivate_user(self, admin_id: int, user_id: int) -> bool:
        """Deactivate user (admin only)"""
        admin = self.user_repository.get_by_id(admin_id)
        if not admin or not admin.is_admin():
            raise ValueError("Only admin users can deactivate users")
        
        # Prevent admin from deactivating themselves
        if admin_id == user_id:
            raise ValueError("Admin cannot deactivate themselves")
        
        return self.user_repository.deactivate_user(user_id)
    
    def activate_user(self, admin_id: int, user_id: int) -> bool:
        """Activate user (admin only)"""
        admin = self.user_repository.get_by_id(admin_id)
        if not admin or not admin.is_admin():
            raise ValueError("Only admin users can activate users")
        
        return self.user_repository.activate_user(user_id)
    
    def get_all_users(self, admin_id: int, include_inactive: bool = False) -> List[User]:
        """Get all users (admin only)"""
        admin = self.user_repository.get_by_id(admin_id)
        if not admin or not admin.is_admin():
            raise ValueError("Only admin users can view all users")
        
        if include_inactive:
            return self.user_repository.get_all()
        else:
            return self.user_repository.get_active_users()
    
    def get_users_by_role(self, admin_id: int, role: str) -> List[User]:
        """Get users by role (admin only)"""
        admin = self.user_repository.get_by_id(admin_id)
        if not admin or not admin.is_admin():
            raise ValueError("Only admin users can filter users by role")
        
        return self.user_repository.get_users_by_role(role)
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        return self.user_repository.get_user_statistics(user_id)
    
    def create_default_admin(self) -> Optional[User]:
        """Create default admin user if none exists"""
        # Check if any admin users exist
        admins = self.user_repository.get_admins()
        if admins:
            return None  # Admin already exists
        
        try:
            admin_user = self.create_user(
                username='admin',
                email='admin@kdpii-labeler.local',
                password='admin123',
                full_name='System Administrator',
                role='admin'
            )
            print(f"Created default admin user: {admin_user.username}")
            return admin_user
        except ValueError:
            # Admin might already exist with different details
            return None
    
    def get_user_dashboard_data(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a user"""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return {}
        
        stats = self.get_user_statistics(user_id)
        
        # Get recent activity - this would be expanded in a real implementation
        recent_activity = []
        
        dashboard_data = {
            'user': user.to_dict(),
            'statistics': stats,
            'recent_activity': recent_activity,
            'permissions': {
                'can_annotate': user.can_annotate(),
                'can_manage_projects': user.can_manage_projects(),
                'is_admin': user.is_admin()
            }
        }
        
        return dashboard_data
    
    def validate_user_permissions(self, user_id: int, required_role: str = None) -> bool:
        """Validate if user has required permissions"""
        user = self.user_repository.get_by_id(user_id)
        if not user or not user.is_active:
            return False
        
        if required_role:
            if required_role == 'admin':
                return user.is_admin()
            elif required_role == 'annotator':
                return user.can_annotate()
        
        return True
    
    def search_users(self, admin_id: int, query: str) -> List[User]:
        """Search users by username or email (admin only)"""
        admin = self.user_repository.get_by_id(admin_id)
        if not admin or not admin.is_admin():
            raise ValueError("Only admin users can search users")
        
        # Simple search implementation
        all_users = self.user_repository.get_active_users()
        query_lower = query.lower()
        
        matching_users = [
            user for user in all_users
            if (query_lower in user.username.lower() or
                query_lower in (user.email or '').lower() or
                query_lower in (user.full_name or '').lower())
        ]
        
        return matching_users