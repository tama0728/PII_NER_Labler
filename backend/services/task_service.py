"""
Task service layer
Business logic for task management and annotation workflow
"""

from typing import Optional, List, Dict, Any, Tuple
from backend.models.task import Task
from backend.repositories.task_repository import TaskRepository
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.user_repository import UserRepository
from backend.services.project_service import ProjectService

class TaskService:
    """Service for task management and annotation workflow"""
    
    def __init__(self):
        self.task_repository = TaskRepository()
        self.project_repository = ProjectRepository()
        self.user_repository = UserRepository()
        self.project_service = ProjectService()
    
    def create_task(self, project_id: int, text: str, user_id: int,
                   original_filename: str = None, line_number: int = None,
                   annotator_id: int = None) -> Task:
        """Create a new task with validation"""
        # Validate access to project
        if not self.project_service.validate_project_access(project_id, user_id, 'write'):
            raise ValueError("User does not have permission to create tasks in this project")
        
        # Validate text
        if not text or len(text.strip()) < 1:
            raise ValueError("Task text cannot be empty")
        
        # Validate annotator if provided
        if annotator_id:
            annotator = self.user_repository.get_by_id(annotator_id)
            if not annotator or not annotator.can_annotate():
                raise ValueError("Invalid annotator or annotator cannot create annotations")
        
        return self.task_repository.create_task_from_text(
            project_id=project_id,
            text=text.strip(),
            original_filename=original_filename,
            line_number=line_number,
            annotator_id=annotator_id
        )
    
    def bulk_create_tasks(self, project_id: int, texts: List[str], user_id: int,
                         original_filename: str = None, annotator_id: int = None) -> List[Task]:
        """Create multiple tasks from text list"""
        if not self.project_service.validate_project_access(project_id, user_id, 'write'):
            raise ValueError("User does not have permission to create tasks in this project")
        
        # Filter and validate texts
        valid_texts = [text.strip() for text in texts if text and text.strip()]
        if not valid_texts:
            raise ValueError("No valid texts provided")
        
        return self.task_repository.bulk_create_from_texts(
            project_id=project_id,
            texts=valid_texts,
            original_filename=original_filename,
            annotator_id=annotator_id
        )
    
    def get_task_by_id(self, task_id: int, user_id: int) -> Optional[Task]:
        """Get task by ID with access control"""
        task = self.task_repository.get_by_id(task_id)
        if not task:
            return None
        
        # Check access to parent project
        if not self.project_service.validate_project_access(task.project_id, user_id, 'read'):
            return None
        
        return task
    
    def get_task_by_uuid(self, task_uuid: str, user_id: int) -> Optional[Task]:
        """Get task by UUID with access control"""
        task = self.task_repository.get_task_by_uuid(task_uuid)
        if not task:
            return None
        
        if not self.project_service.validate_project_access(task.project_id, user_id, 'read'):
            return None
        
        return task
    
    def get_project_tasks(self, project_id: int, user_id: int,
                         completed: Optional[bool] = None,
                         limit: Optional[int] = None,
                         offset: int = 0) -> List[Task]:
        """Get tasks for a project"""
        if not self.project_service.validate_project_access(project_id, user_id, 'read'):
            return []
        
        return self.task_repository.get_tasks_by_project(
            project_id, completed, limit, offset
        )
    
    def get_user_assigned_tasks(self, annotator_id: int, user_id: int,
                              completed: Optional[bool] = None) -> List[Task]:
        """Get tasks assigned to a specific annotator"""
        # User can see their own tasks, admin can see any user's tasks
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return []
        
        if not user.is_admin() and user_id != annotator_id:
            raise ValueError("User can only view their own assigned tasks")
        
        return self.task_repository.get_tasks_by_annotator(annotator_id, completed)
    
    def assign_task_to_user(self, task_id: int, annotator_id: int, assigner_id: int) -> bool:
        """Assign a task to an annotator"""
        task = self.get_task_by_id(task_id, assigner_id)
        if not task:
            return False
        
        # Check permissions
        assigner = self.user_repository.get_by_id(assigner_id)
        if not assigner:
            return False
        
        # Only admin or project owner can assign tasks
        if not assigner.is_admin() and task.project.owner_id != assigner_id:
            raise ValueError("User does not have permission to assign tasks")
        
        # Validate annotator
        annotator = self.user_repository.get_by_id(annotator_id)
        if not annotator or not annotator.can_annotate():
            raise ValueError("Invalid annotator or annotator cannot create annotations")
        
        return self.task_repository.assign_task_to_annotator(task_id, annotator_id)
    
    def get_next_task_for_annotation(self, project_id: int, user_id: int) -> Optional[Task]:
        """Get next task for user to annotate"""
        if not self.project_service.validate_project_access(project_id, user_id, 'read'):
            return None
        
        user = self.user_repository.get_by_id(user_id)
        if not user or not user.can_annotate():
            return None
        
        return self.task_repository.get_next_task_for_annotation(project_id, user_id)
    
    def mark_task_completed(self, task_id: int, user_id: int) -> bool:
        """Mark task as completed"""
        task = self.get_task_by_id(task_id, user_id)
        if not task:
            return False
        
        user = self.user_repository.get_by_id(user_id)
        if not user or not user.can_annotate():
            return False
        
        # User can complete their own tasks, admin can complete any task
        if not user.is_admin() and task.annotator_id != user_id:
            raise ValueError("User can only complete their own assigned tasks")
        
        return self.task_repository.mark_task_completed(task_id, user_id)
    
    def mark_task_incomplete(self, task_id: int, user_id: int) -> bool:
        """Mark task as incomplete"""
        task = self.get_task_by_id(task_id, user_id)
        if not task:
            return False
        
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return False
        
        # User can mark their own tasks incomplete, admin can mark any task incomplete
        if not user.is_admin() and task.annotator_id != user_id:
            raise ValueError("User can only modify their own assigned tasks")
        
        return self.task_repository.mark_task_incomplete(task_id)
    
    def update_task(self, task_id: int, user_id: int, **kwargs) -> Optional[Task]:
        """Update task with access control"""
        task = self.get_task_by_id(task_id, user_id)
        if not task:
            return None
        
        # Check permissions - admin or project owner can update
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return None
        
        if not user.is_admin() and task.project.owner_id != user_id:
            raise ValueError("User does not have permission to update this task")
        
        # Filter allowed fields
        allowed_fields = ['text', 'identifier_type', 'annotator_id']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        # Validate text if provided
        if 'text' in update_data and (not update_data['text'] or len(update_data['text'].strip()) < 1):
            raise ValueError("Task text cannot be empty")
        
        # Validate identifier type
        if 'identifier_type' in update_data and update_data['identifier_type'] not in ['direct', 'quasi', 'default']:
            raise ValueError(f"Invalid identifier type: {update_data['identifier_type']}")
        
        return self.task_repository.update(task_id, **update_data)
    
    def delete_task(self, task_id: int, user_id: int) -> bool:
        """Delete task with access control"""
        task = self.get_task_by_id(task_id, user_id)
        if not task:
            return False
        
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return False
        
        # Only admin or project owner can delete tasks
        if not user.is_admin() and task.project.owner_id != user_id:
            raise ValueError("User does not have permission to delete this task")
        
        return self.task_repository.delete(task_id)
    
    def search_tasks(self, project_id: int, user_id: int, query: str,
                    limit: int = 50) -> List[Task]:
        """Search tasks by text content"""
        if not self.project_service.validate_project_access(project_id, user_id, 'read'):
            return []
        
        return self.task_repository.search_tasks_by_text(project_id, query, limit)
    
    def get_task_statistics(self, project_id: int, user_id: int) -> Dict[str, Any]:
        """Get task statistics for a project"""
        if not self.project_service.validate_project_access(project_id, user_id, 'read'):
            return {}
        
        return self.task_repository.get_task_statistics(project_id)
    
    def get_user_task_progress(self, annotator_id: int, requester_id: int) -> Dict[str, Any]:
        """Get task progress for a user"""
        requester = self.user_repository.get_by_id(requester_id)
        if not requester:
            return {}
        
        # User can see their own progress, admin can see anyone's progress
        if not requester.is_admin() and requester_id != annotator_id:
            raise ValueError("User can only view their own task progress")
        
        return self.task_repository.get_user_task_progress(annotator_id)
    
    def get_annotation_quality_report(self, project_id: int, user_id: int) -> Dict[str, Any]:
        """Get annotation quality report for a project"""
        if not self.project_service.validate_project_access(project_id, user_id, 'read'):
            return {}
        
        return self.task_repository.get_annotation_quality_report(project_id)
    
    def export_project_tasks(self, project_id: int, user_id: int, 
                           export_format: str = 'conll') -> Optional[str]:
        """Export project tasks in specified format"""
        if not self.project_service.validate_project_access(project_id, user_id, 'read'):
            return None
        
        if export_format == 'conll':
            return self.task_repository.export_project_tasks_conll(project_id)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")
    
    def get_tasks_with_label(self, project_id: int, user_id: int, 
                           label_value: str) -> List[Task]:
        """Get tasks containing annotations with specific label"""
        if not self.project_service.validate_project_access(project_id, user_id, 'read'):
            return []
        
        return self.task_repository.get_tasks_with_label(project_id, label_value)
    
    def get_unannotated_tasks(self, project_id: int, user_id: int) -> List[Task]:
        """Get tasks without any annotations"""
        if not self.project_service.validate_project_access(project_id, user_id, 'read'):
            return []
        
        return self.task_repository.get_tasks_without_annotations(project_id)
    
    def validate_task_access(self, task_id: int, user_id: int, 
                           required_permission: str = 'read') -> bool:
        """Validate user access to a task"""
        task = self.task_repository.get_by_id(task_id)
        if not task:
            return False
        
        # Check project access first
        if not self.project_service.validate_project_access(task.project_id, user_id, required_permission):
            return False
        
        # Additional task-specific checks
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return False
        
        # For annotation permissions, check if user can annotate
        if required_permission == 'annotate':
            if not user.can_annotate():
                return False
            # User can annotate unassigned tasks or their own assigned tasks
            return task.annotator_id is None or task.annotator_id == user_id
        
        return True