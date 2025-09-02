"""
Simplified Task service layer - Guest mode
Business logic for task management without authentication
"""

from typing import Optional, List, Dict, Any
from backend.constants import GUEST_USER_ID
from backend.models.task import Task
from backend.repositories.task_repository import TaskRepository
from backend.repositories.project_repository import ProjectRepository

class TaskService:
    """Simplified service for task management in guest mode"""
    
    def __init__(self):
        self.task_repository = TaskRepository()
        self.project_repository = ProjectRepository()
    
    def create_task(self, project_id: int, text: str, user_id: int = GUEST_USER_ID,
                   original_filename: str = None, line_number: int = None,
                   annotator_id: int = None) -> Task:
        """Create a new task with basic validation"""
        # Validate text
        if not text or len(text.strip()) < 1:
            raise ValueError("Task text cannot be empty")
        
        return self.task_repository.create_task_from_text(
            project_id=project_id,
            text=text.strip(),
            original_filename=original_filename,
            line_number=line_number,
            annotator_id=annotator_id
        )
    
    def bulk_create_tasks(self, project_id: int, texts: List[str], user_id: int = GUEST_USER_ID,
                         original_filename: str = None, annotator_id: int = None) -> List[Task]:
        """Create multiple tasks from text list"""
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
    
    def get_task_by_id(self, task_id: int, user_id: int = GUEST_USER_ID) -> Optional[Task]:
        """Get task by ID"""
        return self.task_repository.get_by_id(task_id)
    
    def get_project_tasks(self, project_id: int, user_id: int = GUEST_USER_ID,
                         completed: Optional[bool] = None,
                         limit: Optional[int] = None,
                         offset: int = 0) -> List[Task]:
        """Get tasks for a project"""
        return self.task_repository.get_tasks_by_project(
            project_id, completed, limit, offset
        )
    
    def mark_task_completed(self, task_id: int, user_id: int = GUEST_USER_ID) -> bool:
        """Mark task as completed"""
        return self.task_repository.mark_task_completed(task_id, user_id)
    
    def update_task(self, task_id: int, user_id: int = GUEST_USER_ID, **kwargs) -> Optional[Task]:
        """Update task"""
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
    
    def delete_task(self, task_id: int, user_id: int = GUEST_USER_ID) -> bool:
        """Delete task"""
        return self.task_repository.delete(task_id)
    
    def search_tasks(self, project_id: int, query: str, user_id: int = GUEST_USER_ID,
                    limit: int = 50) -> List[Task]:
        """Search tasks by text content"""
        return self.task_repository.search_tasks_by_text(project_id, query, limit)
    
    def get_task_statistics(self, project_id: int, user_id: int = GUEST_USER_ID) -> Dict[str, Any]:
        """Get task statistics for a project"""
        return self.task_repository.get_task_statistics(project_id)