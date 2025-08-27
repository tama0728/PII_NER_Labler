"""
Annotation repository implementation
Specialized data access for annotation management
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import func, desc, and_, or_
from backend.models.annotation import Annotation
from backend.repositories.base_repository import BaseRepository

class AnnotationRepository(BaseRepository[Annotation]):
    """Repository for annotation-specific database operations"""
    
    def __init__(self):
        super().__init__(Annotation)
    
    def get_annotations_by_task(self, task_id: int) -> List[Annotation]:
        """Get all annotations for a specific task"""
        return self.session.query(Annotation).filter(
            Annotation.task_id == task_id
        ).order_by(Annotation.start).all()
    
    def get_annotation_by_uuid(self, uuid: str) -> Optional[Annotation]:
        """Get annotation by UUID"""
        return self.session.query(Annotation).filter(Annotation.uuid == uuid).first()
    
    def create_annotation(self, task_id: int, start: int, end: int,
                        text: str, labels: List[str],
                        confidence: str = 'high',
                        entity_id: str = None,
                        notes: str = None) -> Annotation:
        """Create a new annotation with validation"""
        # Validate span
        if start >= end:
            raise ValueError(f"Invalid annotation span: start={start}, end={end}")
        
        # Check for exact duplicates
        existing = self.session.query(Annotation).filter(
            Annotation.task_id == task_id,
            Annotation.start == start,
            Annotation.end == end,
            Annotation.labels == labels
        ).first()
        
        if existing:
            return existing
        
        annotation = self.create(
            task_id=task_id,
            start=start,
            end=end,
            text=text,
            labels=labels,
            confidence=confidence,
            entity_id=entity_id,
            notes=notes
        )
        
        return annotation
    
    def get_overlapping_annotations(self, task_id: int, start: int, end: int) -> List[Annotation]:
        """Get annotations that overlap with the given span"""
        return self.session.query(Annotation).filter(
            Annotation.task_id == task_id,
            or_(
                and_(Annotation.start < end, Annotation.end > start),  # Overlapping
                and_(Annotation.start >= start, Annotation.end <= end),  # Contained
                and_(Annotation.start <= start, Annotation.end >= end)   # Containing
            )
        ).all()
    
    def get_annotations_by_label(self, label_value: str, 
                               project_id: int = None) -> List[Annotation]:
        """Get annotations that contain a specific label"""
        query = self.session.query(Annotation).filter(
            Annotation.labels.contains([label_value])
        )
        
        if project_id:
            from backend.models.task import Task
            query = query.join(Task).filter(Task.project_id == project_id)
        
        return query.all()
    
    def get_annotations_by_entity_id(self, entity_id: str) -> List[Annotation]:
        """Get annotations with the same entity ID"""
        return self.session.query(Annotation).filter(
            Annotation.entity_id == entity_id
        ).all()
    
    def link_annotations(self, annotation_id1: int, annotation_id2: int) -> bool:
        """Create bidirectional link between two annotations"""
        ann1 = self.get_by_id(annotation_id1)
        ann2 = self.get_by_id(annotation_id2)
        
        if not ann1 or not ann2:
            return False
        
        # Link them bidirectionally
        ann1.link_to_annotation(ann2.uuid)
        ann2.link_to_annotation(ann1.uuid)
        
        return True
    
    def unlink_annotations(self, annotation_id1: int, annotation_id2: int) -> bool:
        """Remove bidirectional link between two annotations"""
        ann1 = self.get_by_id(annotation_id1)
        ann2 = self.get_by_id(annotation_id2)
        
        if not ann1 or not ann2:
            return False
        
        # Unlink them bidirectionally
        ann1.unlink_from_annotation(ann2.uuid)
        ann2.unlink_from_annotation(ann1.uuid)
        
        return True
    
    def get_related_annotations(self, annotation_id: int) -> List[Annotation]:
        """Get all annotations related to the given annotation"""
        annotation = self.get_by_id(annotation_id)
        if not annotation:
            return []
        
        related_uuids = annotation.related_annotations
        if not related_uuids:
            return []
        
        return self.session.query(Annotation).filter(
            Annotation.uuid.in_(related_uuids)
        ).all()
    
    def update_annotation_labels(self, annotation_id: int, new_labels: List[str]) -> bool:
        """Update annotation labels"""
        annotation = self.get_by_id(annotation_id)
        if annotation:
            annotation.set_labels(new_labels)
            return True
        return False
    
    def update_annotation_confidence(self, annotation_id: int, confidence: str) -> bool:
        """Update annotation confidence"""
        annotation = self.get_by_id(annotation_id)
        if annotation:
            annotation.set_confidence(confidence)
            return True
        return False
    
    def get_annotation_statistics(self, project_id: int = None,
                                task_id: int = None) -> Dict[str, Any]:
        """Get annotation statistics"""
        query = self.session.query(Annotation)
        
        if task_id:
            query = query.filter(Annotation.task_id == task_id)
        elif project_id:
            from backend.models.task import Task
            query = query.join(Task).filter(Task.project_id == project_id)
        
        annotations = query.all()
        
        total_annotations = len(annotations)
        
        # Label distribution
        label_distribution = {}
        for annotation in annotations:
            for label in annotation.labels:
                label_distribution[label] = label_distribution.get(label, 0) + 1
        
        # Confidence distribution
        confidence_distribution = {'high': 0, 'medium': 0, 'low': 0}
        for annotation in annotations:
            confidence_distribution[annotation.confidence] += 1
        
        # Span length statistics
        span_lengths = [annotation.span_length for annotation in annotations]
        avg_span_length = sum(span_lengths) / len(span_lengths) if span_lengths else 0
        
        # Entity relationships
        annotations_with_entities = sum(1 for ann in annotations if ann.entity_id)
        annotations_with_relationships = sum(1 for ann in annotations if ann.related_annotations)
        
        return {
            'project_id': project_id,
            'task_id': task_id,
            'total_annotations': total_annotations,
            'label_distribution': label_distribution,
            'confidence_distribution': confidence_distribution,
            'avg_span_length': avg_span_length,
            'min_span_length': min(span_lengths) if span_lengths else 0,
            'max_span_length': max(span_lengths) if span_lengths else 0,
            'annotations_with_entity_ids': annotations_with_entities,
            'annotations_with_relationships': annotations_with_relationships,
            'unique_entities': len(set(ann.entity_id for ann in annotations if ann.entity_id))
        }
    
    def find_duplicate_annotations(self, task_id: int) -> List[Tuple[Annotation, Annotation]]:
        """Find duplicate annotations in a task"""
        annotations = self.get_annotations_by_task(task_id)
        duplicates = []
        
        for i, ann1 in enumerate(annotations):
            for ann2 in annotations[i+1:]:
                if (ann1.start == ann2.start and 
                    ann1.end == ann2.end and 
                    ann1.labels == ann2.labels):
                    duplicates.append((ann1, ann2))
        
        return duplicates
    
    def remove_duplicate_annotations(self, task_id: int) -> int:
        """Remove duplicate annotations from a task"""
        duplicates = self.find_duplicate_annotations(task_id)
        removed_count = 0
        
        for _, duplicate_ann in duplicates:
            self.delete(duplicate_ann.id)
            removed_count += 1
        
        return removed_count
    
    def get_annotation_conflicts(self, task_id: int) -> List[Dict[str, Any]]:
        """Find potentially conflicting annotations (same span, different labels)"""
        annotations = self.get_annotations_by_task(task_id)
        conflicts = []
        
        for i, ann1 in enumerate(annotations):
            for ann2 in annotations[i+1:]:
                if (ann1.start == ann2.start and 
                    ann1.end == ann2.end and 
                    ann1.labels != ann2.labels):
                    conflicts.append({
                        'span': (ann1.start, ann1.end),
                        'text': ann1.text,
                        'annotation1': ann1.to_dict(),
                        'annotation2': ann2.to_dict(),
                        'conflict_type': 'label_mismatch'
                    })
        
        return conflicts
    
    def export_annotations_for_task(self, task_id: int, format: str = 'label_studio') -> Any:
        """Export annotations for a task in specified format"""
        annotations = self.get_annotations_by_task(task_id)
        
        if format == 'label_studio':
            return [{
                'id': ann.id,
                'created_at': ann.created_at.isoformat(),
                'result': [ann.to_label_studio_result()]
            } for ann in annotations]
        
        elif format == 'conll':
            # This would typically be handled by the task repository
            # but we can provide annotation-specific data
            return [{
                'start': ann.start,
                'end': ann.end,
                'text': ann.text,
                'labels': ann.labels
            } for ann in annotations]
        
        else:
            # Default dictionary format
            return [ann.to_dict() for ann in annotations]
    
    def bulk_update_entity_ids(self, annotation_ids: List[int], entity_id: str) -> int:
        """Bulk update entity IDs for multiple annotations"""
        updated_count = self.session.query(Annotation)\
            .filter(Annotation.id.in_(annotation_ids))\
            .update({Annotation.entity_id: entity_id}, synchronize_session=False)
        
        self.session.commit()
        return updated_count
    
    def get_entity_groups(self, task_id: int) -> Dict[str, List[Annotation]]:
        """Get annotations grouped by entity ID"""
        annotations = self.get_annotations_by_task(task_id)
        entity_groups = {}
        
        for annotation in annotations:
            if annotation.entity_id:
                if annotation.entity_id not in entity_groups:
                    entity_groups[annotation.entity_id] = []
                entity_groups[annotation.entity_id].append(annotation)
        
        return entity_groups