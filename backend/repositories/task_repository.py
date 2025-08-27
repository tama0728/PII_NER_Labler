"""
Task repository implementation
Specialized data access for task management
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import func, desc, asc
from backend.models.task import Task
from backend.models.annotation import Annotation
from backend.repositories.base_repository import BaseRepository

class TaskRepository(BaseRepository[Task]):
    """Repository for task-specific database operations"""
    
    def __init__(self):
        super().__init__(Task)
    
    def get_tasks_by_project(self, project_id: int, 
                           completed: Optional[bool] = None,
                           limit: Optional[int] = None,
                           offset: int = 0) -> List[Task]:
        """Get tasks by project with optional filtering"""
        query = self.session.query(Task).filter(Task.project_id == project_id)
        
        if completed is not None:
            query = query.filter(Task.is_completed == completed)
        
        query = query.order_by(desc(Task.updated_at))
        
        if limit:
            query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def get_tasks_by_annotator(self, annotator_id: int,
                             completed: Optional[bool] = None) -> List[Task]:
        """Get tasks assigned to a specific annotator"""
        query = self.session.query(Task).filter(Task.annotator_id == annotator_id)
        
        if completed is not None:
            query = query.filter(Task.is_completed == completed)
        
        return query.order_by(desc(Task.updated_at)).all()
    
    def get_task_by_uuid(self, uuid: str) -> Optional[Task]:
        """Get task by UUID"""
        return self.session.query(Task).filter(Task.uuid == uuid).first()
    
    def create_task_from_text(self, project_id: int, text: str,
                            original_filename: str = None,
                            line_number: int = None,
                            annotator_id: int = None) -> Task:
        """Create a new task from text"""
        task = self.create(
            project_id=project_id,
            text=text,
            original_filename=original_filename,
            line_number=line_number,
            annotator_id=annotator_id
        )
        return task
    
    def bulk_create_from_texts(self, project_id: int, texts: List[str],
                              original_filename: str = None,
                              annotator_id: int = None) -> List[Task]:
        """Create multiple tasks from a list of texts"""
        task_data = []
        for i, text in enumerate(texts):
            task_data.append({
                'project_id': project_id,
                'text': text,
                'original_filename': original_filename,
                'line_number': i + 1 if original_filename else None,
                'annotator_id': annotator_id
            })
        
        return self.bulk_create(task_data)
    
    def get_next_task_for_annotation(self, project_id: int,
                                   annotator_id: int = None) -> Optional[Task]:
        """Get next incomplete task for annotation"""
        query = self.session.query(Task).filter(
            Task.project_id == project_id,
            Task.is_completed == False
        )
        
        if annotator_id:
            query = query.filter(Task.annotator_id == annotator_id)
        
        return query.order_by(asc(Task.created_at)).first()
    
    def assign_task_to_annotator(self, task_id: int, annotator_id: int) -> bool:
        """Assign a task to an annotator"""
        task = self.get_by_id(task_id)
        if task and not task.is_completed:
            task.annotator_id = annotator_id
            self.session.commit()
            return True
        return False
    
    def mark_task_completed(self, task_id: int, annotator_id: int = None) -> bool:
        """Mark a task as completed"""
        task = self.get_by_id(task_id)
        if task:
            task.mark_completed(annotator_id)
            return True
        return False
    
    def mark_task_incomplete(self, task_id: int) -> bool:
        """Mark a task as incomplete"""
        task = self.get_by_id(task_id)
        if task:
            task.mark_incomplete()
            return True
        return False
    
    def get_task_statistics(self, project_id: int = None) -> Dict[str, Any]:
        """Get task statistics, optionally filtered by project"""
        query = self.session.query(Task)
        
        if project_id:
            query = query.filter(Task.project_id == project_id)
        
        all_tasks = query.all()
        
        total_tasks = len(all_tasks)
        completed_tasks = sum(1 for task in all_tasks if task.is_completed)
        
        # Annotation statistics
        total_annotations = sum(len(task.annotations) for task in all_tasks)
        
        # Tasks with overlapping annotations
        tasks_with_overlaps = sum(1 for task in all_tasks if task.get_overlapping_annotations())
        
        # Identifier type distribution
        identifier_distribution = {}
        for task in all_tasks:
            identifier_distribution[task.identifier_type] = identifier_distribution.get(task.identifier_type, 0) + 1
        
        return {
            'project_id': project_id,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'incomplete_tasks': total_tasks - completed_tasks,
            'completion_percentage': completed_tasks / total_tasks * 100 if total_tasks > 0 else 0,
            'total_annotations': total_annotations,
            'avg_annotations_per_task': total_annotations / total_tasks if total_tasks > 0 else 0,
            'tasks_with_overlapping_annotations': tasks_with_overlaps,
            'identifier_type_distribution': identifier_distribution
        }
    
    def search_tasks_by_text(self, project_id: int, search_query: str,
                           limit: int = 50) -> List[Task]:
        """Search tasks by text content"""
        return self.session.query(Task).filter(
            Task.project_id == project_id,
            Task.text.contains(search_query)
        ).limit(limit).all()
    
    def get_tasks_with_label(self, project_id: int, label_value: str) -> List[Task]:
        """Get tasks that contain annotations with a specific label"""
        # Join with annotations to find tasks containing the label
        tasks_with_label = self.session.query(Task).join(Annotation).filter(
            Task.project_id == project_id,
            Annotation.labels.contains([label_value])
        ).distinct().all()
        
        return tasks_with_label
    
    def get_tasks_without_annotations(self, project_id: int) -> List[Task]:
        """Get tasks that have no annotations"""
        return self.session.query(Task).filter(
            Task.project_id == project_id,
            ~Task.annotations.any()
        ).all()
    
    def get_annotation_quality_report(self, project_id: int) -> Dict[str, Any]:
        """Generate annotation quality report for a project"""
        tasks = self.get_tasks_by_project(project_id)
        
        total_tasks = len(tasks)
        annotated_tasks = sum(1 for task in tasks if task.annotations)
        empty_tasks = total_tasks - annotated_tasks
        
        # Overlapping annotations analysis
        tasks_with_overlaps = [task for task in tasks if task.get_overlapping_annotations()]
        overlap_count = len(tasks_with_overlaps)
        
        # Confidence distribution
        confidence_distribution = {'high': 0, 'medium': 0, 'low': 0}
        for task in tasks:
            for annotation in task.annotations:
                confidence_distribution[annotation.confidence] += 1
        
        return {
            'project_id': project_id,
            'total_tasks': total_tasks,
            'annotated_tasks': annotated_tasks,
            'empty_tasks': empty_tasks,
            'annotation_coverage': annotated_tasks / total_tasks * 100 if total_tasks > 0 else 0,
            'tasks_with_overlapping_annotations': overlap_count,
            'overlap_percentage': overlap_count / total_tasks * 100 if total_tasks > 0 else 0,
            'confidence_distribution': confidence_distribution,
            'avg_annotations_per_task': sum(len(task.annotations) for task in tasks) / total_tasks if total_tasks > 0 else 0
        }
    
    def export_project_tasks_conll(self, project_id: int) -> str:
        """Export all project tasks in CoNLL format"""
        tasks = self.get_tasks_by_project(project_id, completed=True)
        
        conll_output = []
        for task in tasks:
            conll_output.append(f"# Task: {task.uuid}")
            conll_output.append(task.export_conll_format())
            conll_output.append("")  # Empty line between tasks
        
        return "\n".join(conll_output)
    
    def get_user_task_progress(self, annotator_id: int) -> Dict[str, Any]:
        """Get task progress for a specific annotator"""
        tasks = self.get_tasks_by_annotator(annotator_id)
        
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.is_completed)
        
        # Group by project
        project_progress = {}
        for task in tasks:
            project_id = task.project_id
            if project_id not in project_progress:
                project_progress[project_id] = {
                    'total': 0,
                    'completed': 0,
                    'project_name': task.project.name if task.project else 'Unknown'
                }
            
            project_progress[project_id]['total'] += 1
            if task.is_completed:
                project_progress[project_id]['completed'] += 1
        
        # Calculate completion rates
        for project_data in project_progress.values():
            project_data['completion_rate'] = (
                project_data['completed'] / project_data['total'] * 100 
                if project_data['total'] > 0 else 0
            )
        
        return {
            'annotator_id': annotator_id,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': completed_tasks / total_tasks * 100 if total_tasks > 0 else 0,
            'project_progress': project_progress
        }