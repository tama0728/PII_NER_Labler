"""
Project service layer
Business logic for project management
"""

from typing import Optional, List, Dict, Any
from backend.models.project import Project
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.user_repository import UserRepository
class ProjectService:
    """Service for project management"""
    
    def __init__(self):
        self.project_repository = ProjectRepository()
        self.user_repository = UserRepository()
        self._label_service = None
    
    @property
    def label_service(self):
        """Lazy loading of LabelService to avoid circular import"""
        if self._label_service is None:
            from backend.services.label_service import LabelService
            self._label_service = LabelService()
        return self._label_service
    
    def create_project(self, name: str, owner_id: int, description: str = None,
                      **kwargs) -> Project:
        """Create a new project with validation"""
        # Validate input
        if not name or len(name.strip()) < 2:
            raise ValueError("Project name must be at least 2 characters long")
        
        # Verify owner exists and can manage projects
        owner = self.user_repository.get_by_id(owner_id)
        if not owner:
            raise ValueError("Project owner does not exist")
        
        if not owner.can_manage_projects():
            raise ValueError("User does not have permission to create projects")
        
        # Create project with default labels
        project = self.project_repository.create_project_with_default_labels(
            name=name.strip(),
            owner_id=owner_id,
            description=description.strip() if description else None,
            **kwargs
        )
        
        return project
    
    def get_project_by_id(self, project_id: int, user_id: int = None) -> Optional[Project]:
        """Get project by ID with access control"""
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return None
        
        # Check access permissions if user_id provided
        if user_id:
            user = self.user_repository.get_by_id(user_id)
            if not user:
                return None
            
            # Admin can access all projects, others only their own
            if not user.is_admin() and project.owner_id != user_id:
                return None
        
        return project
    
    def get_user_projects(self, user_id: int, active_only: bool = True) -> List[Project]:
        """Get projects owned by user"""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return []
        
        if user.is_admin():
            # Admin sees all projects
            if active_only:
                return self.project_repository.get_active_projects()
            else:
                return self.project_repository.get_all()
        else:
            # Regular users see only their projects
            if active_only:
                return self.project_repository.get_active_projects_by_owner(user_id)
            else:
                return self.project_repository.get_projects_by_owner(user_id)
    
    def update_project(self, project_id: int, user_id: int, **kwargs) -> Optional[Project]:
        """Update project with access control"""
        project = self.get_project_by_id(project_id, user_id)
        if not project:
            return None
        
        # Check permissions
        user = self.user_repository.get_by_id(user_id)
        if not user or (not user.is_admin() and project.owner_id != user_id):
            raise ValueError("User does not have permission to update this project")
        
        # Filter allowed fields
        allowed_fields = ['name', 'description', 'allow_overlapping_annotations', 'require_all_labels']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        # Validate name if provided
        if 'name' in update_data and (not update_data['name'] or len(update_data['name'].strip()) < 2):
            raise ValueError("Project name must be at least 2 characters long")
        
        return self.project_repository.update(project_id, **update_data)
    
    def delete_project(self, project_id: int, user_id: int) -> bool:
        """Delete project with access control"""
        project = self.get_project_by_id(project_id, user_id)
        if not project:
            return False
        
        user = self.user_repository.get_by_id(user_id)
        if not user or (not user.is_admin() and project.owner_id != user_id):
            raise ValueError("User does not have permission to delete this project")
        
        return self.project_repository.delete(project_id)
    
    def deactivate_project(self, project_id: int, user_id: int) -> bool:
        """Deactivate project (soft delete)"""
        project = self.get_project_by_id(project_id, user_id)
        if not project:
            return False
        
        user = self.user_repository.get_by_id(user_id)
        if not user or (not user.is_admin() and project.owner_id != user_id):
            raise ValueError("User does not have permission to deactivate this project")
        
        return self.project_repository.deactivate_project(project_id)
    
    def activate_project(self, project_id: int, user_id: int) -> bool:
        """Activate project"""
        project = self.project_repository.get_by_id(project_id)
        if not project:
            return False
        
        user = self.user_repository.get_by_id(user_id)
        if not user or (not user.is_admin() and project.owner_id != user_id):
            raise ValueError("User does not have permission to activate this project")
        
        return self.project_repository.activate_project(project_id)
    
    def get_project_with_statistics(self, project_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get project with detailed statistics"""
        project = self.get_project_by_id(project_id, user_id)
        if not project:
            return None
        
        return self.project_repository.get_project_with_stats(project_id)
    
    def duplicate_project(self, project_id: int, new_name: str, user_id: int) -> Optional[Project]:
        """Duplicate a project"""
        original_project = self.get_project_by_id(project_id, user_id)
        if not original_project:
            return None
        
        user = self.user_repository.get_by_id(user_id)
        if not user or not user.can_manage_projects():
            raise ValueError("User does not have permission to create projects")
        
        return self.project_repository.duplicate_project(project_id, new_name, user_id)
    
    def search_projects(self, user_id: int, query: str) -> List[Project]:
        """Search projects accessible to user"""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return []
        
        if user.is_admin():
            # Admin can search all projects
            return self.project_repository.search_projects(query)
        else:
            # Regular users search only their projects
            return self.project_repository.search_projects(query, owner_id=user_id)
    
    def get_project_dashboard_data(self, project_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive dashboard data for a project"""
        project_stats = self.get_project_with_statistics(project_id, user_id)
        if not project_stats:
            return None
        
        project = project_stats['project']
        stats = project_stats['statistics']
        
        # Get label information
        labels = self.label_service.get_project_labels(project_id)
        
        dashboard_data = {
            'project': project,
            'statistics': stats,
            'labels': [label.to_dict() for label in labels],
            'recent_activity': project_stats.get('recent_activity', []),
            'progress': {
                'completion_percentage': stats['completion_percentage'],
                'completed_tasks': stats['completed_tasks'],
                'total_tasks': stats['total_tasks'],
                'remaining_tasks': stats['total_tasks'] - stats['completed_tasks']
            }
        }
        
        return dashboard_data
    
    def get_projects_overview(self, user_id: int) -> Dict[str, Any]:
        """Get overview of all user's projects"""
        projects = self.get_user_projects(user_id, active_only=True)
        
        total_projects = len(projects)
        completed_projects = len([p for p in projects if p.completion_percentage == 100.0])
        in_progress_projects = total_projects - completed_projects
        
        total_tasks = sum(p.task_count for p in projects)
        total_annotations = sum(p.annotation_count for p in projects)
        
        project_summaries = []
        for project in projects[:10]:  # Show latest 10 projects
            project_summaries.append({
                'id': project.id,
                'name': project.name,
                'completion_percentage': project.completion_percentage,
                'task_count': project.task_count,
                'annotation_count': project.annotation_count,
                'created_at': project.created_at.isoformat() if project.created_at else None
            })
        
        return {
            'summary': {
                'total_projects': total_projects,
                'completed_projects': completed_projects,
                'in_progress_projects': in_progress_projects,
                'total_tasks': total_tasks,
                'total_annotations': total_annotations
            },
            'recent_projects': project_summaries
        }
    
    def validate_project_access(self, project_id: int, user_id: int, 
                              required_permission: str = 'read') -> bool:
        """Validate user access to project"""
        project = self.project_repository.get_by_id(project_id)
        user = self.user_repository.get_by_id(user_id)
        
        if not project or not user or not user.is_active:
            return False
        
        # Admin has all permissions
        if user.is_admin():
            return True
        
        # Project owner has all permissions
        if project.owner_id == user_id:
            return True
        
        # For other users, check specific permissions
        if required_permission == 'read':
            # For now, only owner and admin can read projects
            # This could be extended to support shared projects
            return False
        elif required_permission in ['write', 'delete']:
            # Only owner and admin can modify/delete
            return False
        
        return False
    
    def get_project_export_data(self, project_id: int, user_id: int, 
                              export_format: str = 'json') -> Optional[Dict[str, Any]]:
        """Get project data for export"""
        if not self.validate_project_access(project_id, user_id, 'read'):
            return None
        
        project_stats = self.get_project_with_statistics(project_id, user_id)
        if not project_stats:
            return None
        
        # This would include tasks, annotations, labels, etc.
        # Implementation would depend on the specific export requirements
        export_data = {
            'project': project_stats['project'],
            'statistics': project_stats['statistics'],
            'export_format': export_format,
            'exported_at': None,  # Would be set during actual export
            'exported_by': user_id
        }
        
        return export_data