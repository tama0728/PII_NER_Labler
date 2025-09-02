"""
Task model for individual annotation tasks
"""

from datetime import datetime
from backend.database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, Text, Integer, ForeignKey
from typing import Optional, List
import uuid

class Task(db.Model):
    """Task model representing individual annotation tasks"""
    
    __tablename__ = 'tasks'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Task content
    text: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255))
    line_number: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Task status
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completion_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Identifier classification (for KDPII requirements)
    identifier_type: Mapped[str] = mapped_column(String(20), default='default')  # direct, quasi, default
    
    # Foreign keys
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), nullable=False)
    annotator_id: Mapped[Optional[int]] = mapped_column(Integer)  # Guest mode - no foreign key constraint
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    # annotator relationship removed - using annotator_id only
    annotations: Mapped[List["Annotation"]] = relationship("Annotation", back_populates="task", cascade="all, delete-orphan")
    
    def mark_completed(self, annotator_id: Optional[int] = None) -> None:
        """Mark task as completed"""
        self.is_completed = True
        self.completion_time = datetime.utcnow()
        if annotator_id:
            self.annotator_id = annotator_id
        db.session.commit()
    
    def mark_incomplete(self) -> None:
        """Mark task as incomplete"""
        self.is_completed = False
        self.completion_time = None
        db.session.commit()
    
    def set_identifier_type(self, identifier_type: str) -> None:
        """Set identifier classification type"""
        if identifier_type not in ['direct', 'quasi', 'default']:
            raise ValueError(f"Invalid identifier type: {identifier_type}")
        self.identifier_type = identifier_type
        db.session.commit()
    
    @property
    def annotation_count(self) -> int:
        """Get number of annotations for this task"""
        return len(self.annotations)
    
    @property
    def entity_count(self) -> int:
        """Get number of unique entities (annotations with different spans)"""
        unique_spans = set()
        for annotation in self.annotations:
            unique_spans.add((annotation.start, annotation.end))
        return len(unique_spans)
    
    def get_overlapping_annotations(self) -> List["Annotation"]:
        """Get annotations that overlap with each other"""
        overlapping = []
        annotations = sorted(self.annotations, key=lambda a: a.start)
        
        for i, ann1 in enumerate(annotations):
            for ann2 in annotations[i+1:]:
                # Check if they overlap (not just touch at edges)
                if ann1.start < ann2.end and ann2.start < ann1.end:
                    if ann1 not in overlapping:
                        overlapping.append(ann1)
                    if ann2 not in overlapping:
                        overlapping.append(ann2)
        
        return overlapping
    
    def export_label_studio_format(self) -> dict:
        """Export task in Label Studio format"""
        return {
            'id': self.id,
            'data': {'text': self.text},
            'annotations': [{
                'id': ann.id,
                'created_at': ann.created_at.isoformat(),
                'result': [{
                    'from_name': 'label',
                    'to_name': 'text',
                    'type': 'labels',
                    'value': {
                        'start': ann.start,
                        'end': ann.end,
                        'text': ann.text,
                        'labels': ann.labels
                    }
                }]
            } for ann in self.annotations],
            'predictions': []
        }
    
    def export_conll_format(self) -> str:
        """Export annotations in CoNLL-2003 format"""
        tokens = self.text.split()
        token_labels = ['O'] * len(tokens)
        
        current_pos = 0
        for token_idx, token in enumerate(tokens):
            token_start = self.text.find(token, current_pos)
            token_end = token_start + len(token)
            
            # Check if token overlaps with any annotation
            for ann in self.annotations:
                if ann.start <= token_start < ann.end or ann.start < token_end <= ann.end:
                    # Use B-I-O tagging scheme
                    if token_start == ann.start:
                        token_labels[token_idx] = f"B-{ann.labels[0]}" if ann.labels else "B-MISC"
                    else:
                        token_labels[token_idx] = f"I-{ann.labels[0]}" if ann.labels else "I-MISC"
                    break
            
            current_pos = token_end
        
        # Format as CoNLL
        conll_lines = []
        for token, label in zip(tokens, token_labels):
            conll_lines.append(f"{token}\t{label}")
        
        return '\n'.join(conll_lines)
    
    def to_dict(self, include_annotations: bool = True) -> dict:
        """Convert to dictionary representation"""
        data = {
            'id': self.id,
            'uuid': self.uuid,
            'text': self.text,
            'original_filename': self.original_filename,
            'line_number': self.line_number,
            'is_completed': self.is_completed,
            'completion_time': self.completion_time.isoformat() if self.completion_time else None,
            'identifier_type': self.identifier_type,
            'project_id': self.project_id,
            'annotator_id': self.annotator_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'annotation_count': self.annotation_count,
            'entity_count': self.entity_count
        }
        
        if include_annotations:
            data['annotations'] = [ann.to_dict() for ann in self.annotations]
        
        return data
    
    def __repr__(self) -> str:
        return f'<Task {self.uuid[:8]}... "{self.text[:50]}...">'