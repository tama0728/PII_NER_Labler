"""
Annotation service layer
Business logic for annotation management and NER operations
"""

from typing import Optional, List, Dict, Any, Tuple
from backend.models.annotation import Annotation
from backend.repositories.annotation_repository import AnnotationRepository
from backend.repositories.task_repository import TaskRepository
from backend.services.task_service import TaskService
from backend.services.user_service import UserService

class AnnotationService:
    """Service for annotation management and NER operations"""
    
    def __init__(self):
        self.annotation_repository = AnnotationRepository()
        self.task_repository = TaskRepository()
        self.task_service = TaskService()
        self.user_service = UserService()
    
    def create_annotation(self, task_id: int, start: int, end: int, text: str,
                         labels: List[str], user_id: int,
                         confidence: str = 'high', entity_id: str = None,
                         notes: str = None) -> Annotation:
        """Create a new annotation with validation"""
        # Validate task access
        if not self.task_service.validate_task_access(task_id, user_id, 'annotate'):
            raise ValueError("User does not have permission to annotate this task")
        
        # Get task to validate text bounds
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        
        # Validate annotation bounds
        if start < 0 or end > len(task.text) or start >= end:
            raise ValueError(f"Invalid annotation span: start={start}, end={end}, text_length={len(task.text)}")
        
        # Validate extracted text matches
        extracted_text = task.text[start:end]
        if extracted_text != text:
            raise ValueError(f"Extracted text '{extracted_text}' does not match provided text '{text}'")
        
        # Validate labels
        if not labels or not all(isinstance(label, str) and label.strip() for label in labels):
            raise ValueError("At least one valid label is required")
        
        # Validate confidence
        if confidence not in ['high', 'medium', 'low']:
            raise ValueError(f"Invalid confidence level: {confidence}")
        
        # Check for project-specific settings (e.g., overlapping annotations allowed)
        project = task.project
        if not project.allow_overlapping_annotations:
            overlapping = self.annotation_repository.get_overlapping_annotations(task_id, start, end)
            if overlapping:
                raise ValueError("Overlapping annotations are not allowed in this project")
        
        return self.annotation_repository.create_annotation(
            task_id=task_id,
            start=start,
            end=end,
            text=text,
            labels=labels,
            confidence=confidence,
            entity_id=entity_id,
            notes=notes
        )
    
    def get_annotation_by_id(self, annotation_id: int, user_id: int) -> Optional[Annotation]:
        """Get annotation by ID with access control"""
        annotation = self.annotation_repository.get_by_id(annotation_id)
        if not annotation:
            return None
        
        # Check task access
        if not self.task_service.validate_task_access(annotation.task_id, user_id, 'read'):
            return None
        
        return annotation
    
    def get_annotation_by_uuid(self, annotation_uuid: str, user_id: int) -> Optional[Annotation]:
        """Get annotation by UUID with access control"""
        annotation = self.annotation_repository.get_annotation_by_uuid(annotation_uuid)
        if not annotation:
            return None
        
        if not self.task_service.validate_task_access(annotation.task_id, user_id, 'read'):
            return None
        
        return annotation
    
    def get_task_annotations(self, task_id: int, user_id: int) -> List[Annotation]:
        """Get all annotations for a task"""
        if not self.task_service.validate_task_access(task_id, user_id, 'read'):
            return []
        
        return self.annotation_repository.get_annotations_by_task(task_id)
    
    def update_annotation(self, annotation_id: int, user_id: int, **kwargs) -> Optional[Annotation]:
        """Update annotation with access control"""
        annotation = self.get_annotation_by_id(annotation_id, user_id)
        if not annotation:
            return None
        
        # Check permissions - admin or annotator can update their own annotations
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            return None
        
        task = annotation.task
        if not user.is_admin() and task.annotator_id != user_id:
            raise ValueError("User can only update their own annotations")
        
        # Filter allowed fields
        allowed_fields = ['labels', 'confidence', 'notes', 'entity_id']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        # Validate labels if provided
        if 'labels' in update_data:
            labels = update_data['labels']
            if not labels or not all(isinstance(label, str) and label.strip() for label in labels):
                raise ValueError("At least one valid label is required")
        
        # Validate confidence if provided
        if 'confidence' in update_data:
            if update_data['confidence'] not in ['high', 'medium', 'low']:
                raise ValueError(f"Invalid confidence level: {update_data['confidence']}")
        
        return self.annotation_repository.update(annotation_id, **update_data)
    
    def delete_annotation(self, annotation_id: int, user_id: int) -> bool:
        """Delete annotation with access control"""
        annotation = self.get_annotation_by_id(annotation_id, user_id)
        if not annotation:
            return False
        
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            return False
        
        # Check permissions
        task = annotation.task
        if not user.is_admin() and task.annotator_id != user_id:
            raise ValueError("User can only delete their own annotations")
        
        return self.annotation_repository.delete(annotation_id)
    
    def link_annotations(self, annotation_id1: int, annotation_id2: int, user_id: int) -> bool:
        """Link two annotations (for relationship annotation)"""
        ann1 = self.get_annotation_by_id(annotation_id1, user_id)
        ann2 = self.get_annotation_by_id(annotation_id2, user_id)
        
        if not ann1 or not ann2:
            return False
        
        # Check if they're in the same task
        if ann1.task_id != ann2.task_id:
            raise ValueError("Can only link annotations within the same task")
        
        # Check permissions
        user = self.user_service.get_user_by_id(user_id)
        if not user or not user.can_annotate():
            return False
        
        task = ann1.task
        if not user.is_admin() and task.annotator_id != user_id:
            raise ValueError("User can only link their own annotations")
        
        return self.annotation_repository.link_annotations(annotation_id1, annotation_id2)
    
    def unlink_annotations(self, annotation_id1: int, annotation_id2: int, user_id: int) -> bool:
        """Unlink two annotations"""
        ann1 = self.get_annotation_by_id(annotation_id1, user_id)
        ann2 = self.get_annotation_by_id(annotation_id2, user_id)
        
        if not ann1 or not ann2:
            return False
        
        user = self.user_service.get_user_by_id(user_id)
        if not user or not user.can_annotate():
            return False
        
        task = ann1.task
        if not user.is_admin() and task.annotator_id != user_id:
            raise ValueError("User can only unlink their own annotations")
        
        return self.annotation_repository.unlink_annotations(annotation_id1, annotation_id2)
    
    def get_related_annotations(self, annotation_id: int, user_id: int) -> List[Annotation]:
        """Get annotations related to the given annotation"""
        if not self.get_annotation_by_id(annotation_id, user_id):
            return []
        
        return self.annotation_repository.get_related_annotations(annotation_id)
    
    def set_entity_id(self, annotation_id: int, entity_id: str, user_id: int) -> bool:
        """Set entity ID for annotation (for entity relationship tracking)"""
        annotation = self.get_annotation_by_id(annotation_id, user_id)
        if not annotation:
            return False
        
        user = self.user_service.get_user_by_id(user_id)
        if not user or not user.can_annotate():
            return False
        
        task = annotation.task
        if not user.is_admin() and task.annotator_id != user_id:
            raise ValueError("User can only modify their own annotations")
        
        annotation.set_entity_id(entity_id)
        return True
    
    def get_annotations_by_entity_id(self, entity_id: str, user_id: int) -> List[Annotation]:
        """Get annotations with the same entity ID"""
        annotations = self.annotation_repository.get_annotations_by_entity_id(entity_id)
        
        # Filter by access permissions
        accessible_annotations = []
        for annotation in annotations:
            if self.task_service.validate_task_access(annotation.task_id, user_id, 'read'):
                accessible_annotations.append(annotation)
        
        return accessible_annotations
    
    def get_project_annotations_by_label(self, project_id: int, label_value: str, 
                                       user_id: int) -> List[Annotation]:
        """Get annotations with specific label in a project"""
        from backend.services.project_service import ProjectService
        project_service = ProjectService()
        
        if not project_service.validate_project_access(project_id, user_id, 'read'):
            return []
        
        return self.annotation_repository.get_annotations_by_label(label_value, project_id)
    
    def get_annotation_statistics(self, project_id: int = None, task_id: int = None,
                                user_id: int = None) -> Dict[str, Any]:
        """Get annotation statistics with access control"""
        if task_id:
            if not self.task_service.validate_task_access(task_id, user_id, 'read'):
                return {}
        elif project_id:
            from backend.services.project_service import ProjectService
            project_service = ProjectService()
            if not project_service.validate_project_access(project_id, user_id, 'read'):
                return {}
        
        return self.annotation_repository.get_annotation_statistics(project_id, task_id)
    
    def find_overlapping_annotations(self, task_id: int, start: int, end: int,
                                   user_id: int) -> List[Annotation]:
        """Find annotations that overlap with given span"""
        if not self.task_service.validate_task_access(task_id, user_id, 'read'):
            return []
        
        return self.annotation_repository.get_overlapping_annotations(task_id, start, end)
    
    def remove_duplicate_annotations(self, task_id: int, user_id: int) -> int:
        """Remove duplicate annotations from a task"""
        if not self.task_service.validate_task_access(task_id, user_id, 'annotate'):
            raise ValueError("User does not have permission to modify annotations in this task")
        
        return self.annotation_repository.remove_duplicate_annotations(task_id)
    
    def get_annotation_conflicts(self, task_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Find potentially conflicting annotations in a task"""
        if not self.task_service.validate_task_access(task_id, user_id, 'read'):
            return []
        
        return self.annotation_repository.get_annotation_conflicts(task_id)
    
    def bulk_update_entity_ids(self, annotation_ids: List[int], entity_id: str,
                             user_id: int) -> int:
        """Bulk update entity IDs for multiple annotations"""
        # Validate access to all annotations
        for annotation_id in annotation_ids:
            if not self.get_annotation_by_id(annotation_id, user_id):
                raise ValueError(f"User does not have access to annotation {annotation_id}")
        
        user = self.user_service.get_user_by_id(user_id)
        if not user or not user.can_annotate():
            raise ValueError("User does not have permission to modify annotations")
        
        return self.annotation_repository.bulk_update_entity_ids(annotation_ids, entity_id)
    
    def get_entity_groups(self, task_id: int, user_id: int) -> Dict[str, List[Annotation]]:
        """Get annotations grouped by entity ID for a task"""
        if not self.task_service.validate_task_access(task_id, user_id, 'read'):
            return {}
        
        return self.annotation_repository.get_entity_groups(task_id)
    
    def export_task_annotations(self, task_id: int, user_id: int, 
                              export_format: str = 'label_studio') -> Optional[Any]:
        """Export annotations for a task"""
        if not self.task_service.validate_task_access(task_id, user_id, 'read'):
            return None
        
        return self.annotation_repository.export_annotations_for_task(task_id, export_format)
    
    def validate_annotation_data(self, task_id: int, start: int, end: int, 
                               labels: List[str]) -> Tuple[bool, str]:
        """Validate annotation data before creation"""
        try:
            task = self.task_repository.get_by_id(task_id)
            if not task:
                return False, "Task not found"
            
            if start < 0 or end > len(task.text) or start >= end:
                return False, f"Invalid span: start={start}, end={end}, text_length={len(task.text)}"
            
            if not labels or not all(isinstance(label, str) and label.strip() for label in labels):
                return False, "At least one valid label is required"
            
            return True, "Valid annotation data"
        
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_annotation_suggestions(self, task_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get annotation suggestions for a task (placeholder for ML integration)"""
        if not self.task_service.validate_task_access(task_id, user_id, 'read'):
            return []
        
        # This is a placeholder for future ML-based annotation suggestions
        # Could integrate with spaCy, transformers, or custom NER models
        suggestions = []
        
        return suggestions