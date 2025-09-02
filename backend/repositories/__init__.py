"""
Repository pattern implementations
Data access layer abstraction
"""

from backend.repositories.base_repository import BaseRepository
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.task_repository import TaskRepository
from backend.repositories.annotation_repository import AnnotationRepository
from backend.repositories.label_repository import LabelRepository

__all__ = [
    'BaseRepository', 
    'ProjectRepository', 
    'TaskRepository', 
    'AnnotationRepository', 
    'LabelRepository'
]