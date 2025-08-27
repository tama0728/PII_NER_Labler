"""
Label model for NER label definitions
"""

from datetime import datetime
from backend.database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, Boolean
from typing import Optional, List

class Label(db.Model):
    """Label model for NER label definitions"""
    
    __tablename__ = 'labels'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Label definition
    value: Mapped[str] = mapped_column(String(50), nullable=False)
    background: Mapped[str] = mapped_column(String(7), nullable=False, default='#999999')  # Hex color
    hotkey: Mapped[Optional[str]] = mapped_column(String(1))
    
    # Label metadata
    category: Mapped[Optional[str]] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
    example: Mapped[Optional[str]] = mapped_column(Text)
    
    # Display settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Project association
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="labels")
    
    # Unique constraint: value must be unique within project
    __table_args__ = (
        db.UniqueConstraint('project_id', 'value', name='uq_project_label_value'),
        db.UniqueConstraint('project_id', 'hotkey', name='uq_project_label_hotkey'),
    )
    
    def validate_hotkey(self, hotkey: str) -> bool:
        """Validate hotkey format"""
        if not hotkey:
            return True
        return len(hotkey) == 1 and (hotkey.isalnum() or hotkey in '!@#$%^&*()')
    
    def validate_color(self, color: str) -> bool:
        """Validate hex color format"""
        if not color.startswith('#') or len(color) != 7:
            return False
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False
    
    def set_hotkey(self, hotkey: Optional[str]) -> None:
        """Set hotkey with validation"""
        if hotkey and not self.validate_hotkey(hotkey):
            raise ValueError(f"Invalid hotkey format: {hotkey}")
        self.hotkey = hotkey
        db.session.commit()
    
    def set_background_color(self, color: str) -> None:
        """Set background color with validation"""
        if not self.validate_color(color):
            raise ValueError(f"Invalid color format: {color}. Must be hex format like #FF5733")
        self.background = color
        db.session.commit()
    
    def deactivate(self) -> None:
        """Deactivate this label"""
        self.is_active = False
        db.session.commit()
    
    def activate(self) -> None:
        """Activate this label"""
        self.is_active = True
        db.session.commit()
    
    def get_usage_count(self) -> int:
        """Get count of annotations using this label"""
        from backend.models.annotation import Annotation
        count = 0
        
        # Get all tasks in this project
        for task in self.project.tasks:
            for annotation in task.annotations:
                if self.value in annotation.labels:
                    count += 1
        
        return count
    
    def can_be_deleted(self) -> bool:
        """Check if label can be safely deleted"""
        return self.get_usage_count() == 0
    
    @classmethod
    def create_default_labels(cls, project_id: int) -> List["Label"]:
        """Create default NER labels for a project"""
        default_labels = [
            {'value': 'PER', 'background': '#FF5733', 'hotkey': '1', 
             'category': 'Person', 'description': 'Person names', 
             'example': 'John Smith, Mary Johnson'},
            {'value': 'ORG', 'background': '#FF8C00', 'hotkey': '2', 
             'category': 'Organization', 'description': 'Organization names', 
             'example': 'Microsoft, Google, United Nations'},
            {'value': 'LOC', 'background': '#FFD700', 'hotkey': '3', 
             'category': 'Location', 'description': 'Location names', 
             'example': 'New York, Seoul, Mount Everest'},
            {'value': 'MISC', 'background': '#32CD32', 'hotkey': '4', 
             'category': 'Miscellaneous', 'description': 'Other named entities', 
             'example': 'Nobel Prize, iPhone, Christmas'}
        ]
        
        created_labels = []
        for i, label_data in enumerate(default_labels):
            label = cls(
                project_id=project_id,
                sort_order=i,
                **label_data
            )
            db.session.add(label)
            created_labels.append(label)
        
        db.session.commit()
        return created_labels
    
    def to_dict(self, include_usage: bool = False) -> dict:
        """Convert to dictionary representation"""
        data = {
            'id': self.id,
            'value': self.value,
            'background': self.background,
            'hotkey': self.hotkey,
            'category': self.category,
            'description': self.description,
            'example': self.example,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'project_id': self.project_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_usage:
            data['usage_count'] = self.get_usage_count()
            data['can_be_deleted'] = self.can_be_deleted()
        
        return data
    
    def to_label_studio_format(self) -> dict:
        """Convert to Label Studio format"""
        result = {
            'value': self.value,
            'background': self.background
        }
        if self.hotkey:
            result['hotkey'] = self.hotkey
        return result
    
    def __repr__(self) -> str:
        return f'<Label {self.value} ({self.background})>'