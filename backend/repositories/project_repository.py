"""
Project repository implementation
Specialized data access for project management
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import func, desc
from backend.models.project import Project
from backend.models.task import Task
from backend.repositories.base_repository import BaseRepository

class ProjectRepository(BaseRepository[Project]):
    """Repository for project-specific database operations"""
    
    def __init__(self):
        super().__init__(Project)
    
    def get_projects_by_owner(self, owner_id: int) -> List[Project]:
        """Get all projects owned by a specific user"""
        return self.session.query(Project).filter(Project.owner_id == owner_id).all()
    
    def get_active_projects(self) -> List[Project]:
        """Get all active projects"""
        return self.session.query(Project).filter(Project.is_active == True).all()
    
    def get_active_projects_by_owner(self, owner_id: int) -> List[Project]:
        """Get active projects owned by a specific user"""
        return self.session.query(Project).filter(
            Project.owner_id == owner_id,
            Project.is_active == True
        ).all()
    
    def create_project_with_default_labels(self, name: str, owner_id: int, 
                                         description: str = None, **kwargs) -> Project:
        """Create a new project with default labels"""
        project = self.create(
            name=name,
            owner_id=owner_id,
            description=description,
            **kwargs
        )
        
        # Create default labels for the project
        from backend.models.label import Label
        Label.create_default_labels(project.id)
        
        return project
    
    def get_project_with_stats(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project with detailed statistics"""
        project = self.get_by_id(project_id)
        if not project:
            return None
        
        # Get task statistics
        total_tasks = len(project.tasks)
        completed_tasks = sum(1 for task in project.tasks if task.is_completed)
        
        # Get annotation statistics
        total_annotations = sum(len(task.annotations) for task in project.tasks)
        
        # Get label distribution
        label_distribution = project.get_label_distribution()
        
        # Get recent activity (last 10 updated tasks)
        recent_tasks = (self.session.query(Task)
                       .filter(Task.project_id == project_id)
                       .order_by(desc(Task.updated_at))
                       .limit(10)
                       .all())
        
        return {
            'project': project.to_dict(),
            'statistics': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'completion_percentage': project.completion_percentage,
                'total_annotations': total_annotations,
                'label_distribution': label_distribution,
                'total_labels': len(project.labels)
            },
            'recent_activity': [task.to_dict(include_annotations=False) for task in recent_tasks]
        }
    
    def search_projects(self, query: str, owner_id: Optional[int] = None) -> List[Project]:
        """Search projects by name or description"""
        search_filter = Project.name.contains(query) | Project.description.contains(query)
        
        if owner_id:
            search_filter = search_filter & (Project.owner_id == owner_id)
        
        return self.session.query(Project).filter(search_filter).all()
    
    def get_projects_by_completion_status(self, completed: bool = True) -> List[Project]:
        """Get projects by completion status"""
        projects = self.get_active_projects()
        
        if completed:
            return [p for p in projects if p.completion_percentage == 100.0]
        else:
            return [p for p in projects if p.completion_percentage < 100.0]
    
    def get_project_progress_summary(self, project_ids: List[int] = None) -> List[Dict[str, Any]]:
        """Get progress summary for multiple projects"""
        query = self.session.query(Project)
        
        if project_ids:
            query = query.filter(Project.id.in_(project_ids))
        
        projects = query.all()
        summary = []
        
        for project in projects:
            summary.append({
                'id': project.id,
                'name': project.name,
                'owner_id': project.owner_id,
                'task_count': project.task_count,
                'completed_task_count': project.completed_task_count,
                'completion_percentage': project.completion_percentage,
                'annotation_count': project.annotation_count,
                'is_active': project.is_active,
                'created_at': project.created_at.isoformat() if project.created_at else None
            })
        
        return summary
    
    def deactivate_project(self, project_id: int) -> bool:
        """Deactivate a project"""
        project = self.get_by_id(project_id)
        if project:
            project.is_active = False
            self.session.commit()
            return True
        return False
    
    def activate_project(self, project_id: int) -> bool:
        """Activate a project"""
        project = self.get_by_id(project_id)
        if project:
            project.is_active = True
            self.session.commit()
            return True
        return False
    
    def duplicate_project(self, project_id: int, new_name: str, owner_id: int) -> Optional[Project]:
        """Duplicate a project with all its labels (but not tasks)"""
        original_project = self.get_by_id(project_id)
        if not original_project:
            return None
        
        # Create new project
        new_project = self.create(
            name=new_name,
            description=f"Copy of {original_project.description}" if original_project.description else f"Copy of {original_project.name}",
            owner_id=owner_id,
            allow_overlapping_annotations=original_project.allow_overlapping_annotations,
            require_all_labels=original_project.require_all_labels
        )
        
        # Copy labels
        from backend.repositories.label_repository import LabelRepository
        label_repo = LabelRepository()
        
        for label in original_project.labels:
            label_repo.create(
                project_id=new_project.id,
                value=label.value,
                background=label.background,
                hotkey=label.hotkey,
                category=label.category,
                description=label.description,
                example=label.example,
                sort_order=label.sort_order
            )
        
        return new_project
    
    def get_user_project_stats(self, owner_id: int) -> Dict[str, Any]:
        """Get project statistics for a specific user"""
        projects = self.get_projects_by_owner(owner_id)
        
        total_projects = len(projects)
        active_projects = len([p for p in projects if p.is_active])
        completed_projects = len([p for p in projects if p.completion_percentage == 100.0])
        
        total_tasks = sum(p.task_count for p in projects)
        total_annotations = sum(p.annotation_count for p in projects)
        
        return {
            'owner_id': owner_id,
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'completion_rate': completed_projects / total_projects * 100 if total_projects > 0 else 0,
            'total_tasks': total_tasks,
            'total_annotations': total_annotations,
            'avg_tasks_per_project': total_tasks / total_projects if total_projects > 0 else 0,
            'avg_annotations_per_project': total_annotations / total_projects if total_projects > 0 else 0
        }