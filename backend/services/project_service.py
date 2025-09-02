"""
Simplified Project service layer - Guest mode
Business logic for project management without authentication
"""

from typing import Optional, List, Dict, Any
from backend.constants import GUEST_USER_ID
from backend.models.project import Project
from backend.repositories.project_repository import ProjectRepository

class ProjectService:
    """Simplified service for project management in guest mode"""
    
    def __init__(self):
        self.project_repository = ProjectRepository()
    
    def create_project(self, name: str, owner_id: int = GUEST_USER_ID, description: str = None,
                      **kwargs) -> Project:
        """Create a new project with basic validation"""
        # Validate input
        if not name or len(name.strip()) < 2:
            raise ValueError("Project name must be at least 2 characters long")
        
        # Create project with default labels
        project = self.project_repository.create_project_with_default_labels(
            name=name.strip(),
            owner_id=owner_id,
            description=description.strip() if description else None,
            **kwargs
        )
        
        return project
    
    def get_project_by_id(self, project_id: int, user_id: int = GUEST_USER_ID) -> Optional[Project]:
        """Get project by ID"""
        return self.project_repository.get_by_id(project_id)
    
    def get_user_projects(self, user_id: int = GUEST_USER_ID, active_only: bool = True) -> List[Project]:
        """Get all projects"""
        if active_only:
            return self.project_repository.get_active_projects()
        else:
            return self.project_repository.get_all()
    
    def update_project(self, project_id: int, user_id: int = GUEST_USER_ID, **kwargs) -> Optional[Project]:
        """Update project"""
        # Filter allowed fields
        allowed_fields = ['name', 'description', 'allow_overlapping_annotations', 'require_all_labels']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        # Validate name if provided
        if 'name' in update_data and (not update_data['name'] or len(update_data['name'].strip()) < 2):
            raise ValueError("Project name must be at least 2 characters long")
        
        return self.project_repository.update(project_id, **update_data)
    
    def delete_project(self, project_id: int, user_id: int = GUEST_USER_ID) -> bool:
        """Delete project"""
        return self.project_repository.delete(project_id)
    
    def validate_project_access(self, project_id: int, user_id: int, access_type: str) -> bool:
        """Simplified access validation for guest mode"""
        # Guest mode에서는 모든 접근 허용
        return True
    
    def get_project_dashboard_data(self, project_id: int, user_id: int = GUEST_USER_ID) -> Optional[Dict[str, Any]]:
        """Get comprehensive dashboard data for a project"""
        project_stats = self.project_repository.get_project_with_stats(project_id)
        if not project_stats:
            return None
        
        return project_stats