"""
Project model for organizing annotation tasks
"""

from datetime import datetime
from backend.database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, Text, Integer, ForeignKey
from typing import Optional, List

class Project(db.Model):
    """Project model for grouping related annotation tasks"""
    
    __tablename__ = 'projects'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Project settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_overlapping_annotations: Mapped[bool] = mapped_column(Boolean, default=True)
    require_all_labels: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Ownership and timestamps
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="projects")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    labels: Mapped[List["Label"]] = relationship("Label", back_populates="project", cascade="all, delete-orphan")
    
    @property
    def task_count(self) -> int:
        """Get total number of tasks in this project"""
        return len(self.tasks)
    
    @property
    def completed_task_count(self) -> int:
        """Get number of completed tasks"""
        return sum(1 for task in self.tasks if task.is_completed)
    
    @property
    def completion_percentage(self) -> float:
        """Get completion percentage"""
        if not self.tasks:
            return 0.0
        return (self.completed_task_count / self.task_count) * 100.0
    
    @property
    def annotation_count(self) -> int:
        """Get total number of annotations in this project"""
        return sum(len(task.annotations) for task in self.tasks)
    
    def get_label_distribution(self) -> dict:
        """Get distribution of labels across all tasks"""
        label_counts = {}
        for task in self.tasks:
            for annotation in task.annotations:
                for label_value in annotation.labels:
                    label_counts[label_value] = label_counts.get(label_value, 0) + 1
        return label_counts
    
    def to_dict(self, include_stats: bool = False) -> dict:
        """Convert to dictionary representation"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'allow_overlapping_annotations': self.allow_overlapping_annotations,
            'require_all_labels': self.require_all_labels,
            'owner_id': self.owner_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_stats:
            data.update({
                'task_count': self.task_count,
                'completed_task_count': self.completed_task_count,
                'completion_percentage': self.completion_percentage,
                'annotation_count': self.annotation_count,
                'label_distribution': self.get_label_distribution()
            })
        
        return data
    
    def __repr__(self) -> str:
        return f'<Project {self.name}>'