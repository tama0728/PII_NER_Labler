"""
Label service layer - simplified implementation
"""

from typing import List, Optional, Dict, Any
from backend.constants import GUEST_USER_ID
from backend.models.label import Label
from backend.repositories.label_repository import LabelRepository
class LabelService:
    def __init__(self):
        self.label_repository = LabelRepository()
        self._project_service = None
    
    @property
    def project_service(self):
        """Lazy loading of ProjectService to avoid circular import"""
        if self._project_service is None:
            from backend.services.project_service import ProjectService
            self._project_service = ProjectService()
        return self._project_service
    
    def get_project_labels(self, project_id: int, user_id: int = None) -> List[Label]:
        """Get labels for a project"""
        if user_id and not self.project_service.validate_project_access(project_id, user_id, 'read'):
            return []
        return self.label_repository.get_labels_by_project(project_id)
    
    def create_label(self, project_id: int, value: str, user_id: int, **kwargs) -> Label:
        """Create a new label"""
        if not self.project_service.validate_project_access(project_id, user_id, 'write'):
            raise ValueError("User does not have permission to create labels")
        return self.label_repository.create_project_label(project_id, value, **kwargs)
    
    def update_label(self, label_id: int, user_id: int, **kwargs) -> Optional[Label]:
        """Update label with access control"""
        label = self.label_repository.get_by_id(label_id)
        if not label:
            return None
        if not self.project_service.validate_project_access(label.project_id, user_id, 'write'):
            raise ValueError("Permission denied")
        return self.label_repository.update(label_id, **kwargs)
    
    def delete_label(self, label_id: int, user_id: int) -> bool:
        """Delete label"""
        label = self.label_repository.get_by_id(label_id)
        if not label:
            return False
        if not self.project_service.validate_project_access(label.project_id, user_id, 'write'):
            raise ValueError("Permission denied")
        return self.label_repository.delete(label_id)