"""
Annotation model for NER annotations
"""

from datetime import datetime
from backend.database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, JSON
from typing import List
import uuid

class Annotation(db.Model):
    """Annotation model for named entity annotations"""
    
    __tablename__ = 'annotations'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Annotation span
    start: Mapped[int] = mapped_column(Integer, nullable=False)
    end: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Labels (can be multiple for multi-label scenarios)
    labels: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    
    # Confidence and metadata
    confidence: Mapped[str] = mapped_column(String(10), default='high')  # high, medium, low
    notes: Mapped[str] = mapped_column(Text)
    
    # Advanced NER features (GitHub integration)
    identifier_type: Mapped[str] = mapped_column(String(20), default='default')  # direct, quasi, default
    overlapping: Mapped[bool] = mapped_column(db.Boolean, default=False)  # Overlapping annotation flag
    
    # Relationships and entities (for entity relationship annotation)
    related_annotations: Mapped[List[str]] = mapped_column(JSON, default=list)
    entity_id: Mapped[str] = mapped_column(String(36))
    relationships: Mapped[List[dict]] = mapped_column(JSON, default=list)  # Entity relationships data
    
    # Foreign keys
    task_id: Mapped[int] = mapped_column(ForeignKey('tasks.id'), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="annotations")
    
    def __post_init__(self):
        """Post-initialization validation"""
        if self.start >= self.end:
            raise ValueError(f"Invalid annotation span: start={self.start}, end={self.end}")
    
    def set_confidence(self, confidence: str) -> None:
        """Set annotation confidence level"""
        if confidence not in ['high', 'medium', 'low']:
            raise ValueError(f"Invalid confidence level: {confidence}")
        self.confidence = confidence
        db.session.commit()
    
    def add_label(self, label: str) -> None:
        """Add a label to this annotation"""
        if label not in self.labels:
            self.labels = self.labels + [label]  # Create new list for SQLAlchemy to detect change
            db.session.commit()
    
    def remove_label(self, label: str) -> None:
        """Remove a label from this annotation"""
        if label in self.labels:
            new_labels = [l for l in self.labels if l != label]
            self.labels = new_labels
            db.session.commit()
    
    def set_labels(self, labels: List[str]) -> None:
        """Set all labels for this annotation"""
        self.labels = labels
        db.session.commit()
    
    def link_to_annotation(self, other_annotation_id: str) -> None:
        """Create relationship link to another annotation"""
        if other_annotation_id not in self.related_annotations:
            self.related_annotations = self.related_annotations + [other_annotation_id]
            db.session.commit()
    
    def unlink_from_annotation(self, other_annotation_id: str) -> None:
        """Remove relationship link to another annotation"""
        if other_annotation_id in self.related_annotations:
            new_related = [aid for aid in self.related_annotations if aid != other_annotation_id]
            self.related_annotations = new_related
            db.session.commit()
    
    def set_entity_id(self, entity_id: str) -> None:
        """Set entity identifier for relationship tracking"""
        self.entity_id = entity_id
        db.session.commit()
    
    def set_identifier_type(self, identifier_type: str) -> None:
        """Set privacy identifier type (direct/quasi/default)"""
        if identifier_type not in ['direct', 'quasi', 'default']:
            raise ValueError(f"Invalid identifier type: {identifier_type}")
        self.identifier_type = identifier_type
        db.session.commit()
    
    def set_overlapping(self, overlapping: bool) -> None:
        """Set overlapping annotation flag"""
        self.overlapping = overlapping
        db.session.commit()
    
    def add_relationship(self, entity_id: str, relationship_type: str) -> None:
        """Add entity relationship"""
        relationship = {
            'entity_id': entity_id,
            'type': relationship_type,
            'created_at': datetime.utcnow().isoformat()
        }
        if relationship not in self.relationships:
            self.relationships = self.relationships + [relationship]
            db.session.commit()
    
    @property
    def span_length(self) -> int:
        """Get length of annotated text span"""
        return self.end - self.start
    
    def overlaps_with(self, other: "Annotation") -> bool:
        """Check if this annotation overlaps with another"""
        return not (self.end <= other.start or self.start >= other.end)
    
    def contains(self, other: "Annotation") -> bool:
        """Check if this annotation completely contains another"""
        return self.start <= other.start and self.end >= other.end
    
    def is_contained_by(self, other: "Annotation") -> bool:
        """Check if this annotation is completely contained by another"""
        return other.contains(self)
    
    def to_dict(self, include_relationships: bool = True) -> dict:
        """Convert to dictionary representation"""
        data = {
            'id': self.id,
            'uuid': self.uuid,
            'start': self.start,
            'end': self.end,
            'text': self.text,
            'labels': self.labels,
            'confidence': self.confidence,
            'notes': self.notes,
            'entity_id': self.entity_id,
            'task_id': self.task_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'span_length': self.span_length,
            # Advanced NER features
            'identifier_type': self.identifier_type,
            'overlapping': self.overlapping,
            'relationships': self.relationships
        }
        
        if include_relationships:
            data['related_annotations'] = self.related_annotations
        
        return data
    
    def to_label_studio_result(self) -> dict:
        """Convert to Label Studio result format"""
        return {
            'from_name': 'label',
            'to_name': 'text',
            'type': 'labels',
            'value': {
                'start': self.start,
                'end': self.end,
                'text': self.text,
                'labels': self.labels
            }
        }
    
    def __repr__(self) -> str:
        labels_str = ','.join(self.labels) if self.labels else 'no-labels'
        return f'<Annotation {self.uuid[:8]}... "{self.text}" [{labels_str}]>'