"""
Simplified Annotation service layer - Guest mode
Business logic for annotation management without authentication
"""

from typing import Optional, List, Dict, Any
from backend.constants import GUEST_USER_ID
from backend.models.annotation import Annotation
from backend.repositories.annotation_repository import AnnotationRepository
from backend.repositories.task_repository import TaskRepository

class AnnotationService:
    """Simplified service for annotation management in guest mode"""
    
    def __init__(self):
        self.annotation_repository = AnnotationRepository()
        self.task_repository = TaskRepository()
    
    def create_annotation(self, task_id: int, start: int, end: int, text: str,
                         labels: List[str], user_id: int = GUEST_USER_ID,
                         confidence: str = 'high', entity_id: str = None,
                         notes: str = None) -> Annotation:
        """Create a new annotation with basic validation"""
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
    
    def get_annotation_by_id(self, annotation_id: int, user_id: int = GUEST_USER_ID) -> Optional[Annotation]:
        """Get annotation by ID"""
        return self.annotation_repository.get_by_id(annotation_id)
    
    def get_task_annotations(self, task_id: int, user_id: int = GUEST_USER_ID) -> List[Annotation]:
        """Get all annotations for a task"""
        return self.annotation_repository.get_annotations_by_task(task_id)
    
    def update_annotation(self, annotation_id: int, user_id: int = GUEST_USER_ID, **kwargs) -> Optional[Annotation]:
        """Update annotation"""
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
    
    def delete_annotation(self, annotation_id: int, user_id: int = GUEST_USER_ID) -> bool:
        """Delete annotation"""
        return self.annotation_repository.delete(annotation_id)
    
    def get_annotation_statistics(self, project_id: int = None, task_id: int = None,
                                user_id: int = GUEST_USER_ID) -> Dict[str, Any]:
        """Get annotation statistics"""
        return self.annotation_repository.get_annotation_statistics(project_id, task_id)
    
    def find_overlapping_annotations(self, task_id: int, start: int, end: int,
                                   user_id: int = GUEST_USER_ID) -> List[Annotation]:
        """Find annotations that overlap with given span"""
        return self.annotation_repository.get_overlapping_annotations(task_id, start, end)