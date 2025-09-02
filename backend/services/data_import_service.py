"""
Data import service - simplified implementation
"""

import json
from typing import List, Dict, Any, Optional
from backend.constants import GUEST_USER_ID
from backend.services.project_service import ProjectService
from backend.services.task_service import TaskService

class DataImportService:
    def __init__(self):
        self.project_service = ProjectService()
        self.task_service = TaskService()
    
    def import_jsonl_data(self, project_id: int, jsonl_data: str, user_id: int) -> Dict[str, Any]:
        """Import JSONL data as tasks"""
        if not self.project_service.validate_project_access(project_id, user_id, 'write'):
            raise ValueError("Permission denied")
        
        lines = jsonl_data.strip().split('\n')
        texts = []
        
        for line in lines:
            try:
                data = json.loads(line)
                if 'text' in data:
                    texts.append(data['text'])
            except json.JSONDecodeError:
                continue
        
        if not texts:
            raise ValueError("No valid text data found in JSONL")
        
        tasks = self.task_service.bulk_create_tasks(project_id, texts, user_id)
        
        return {
            'imported_count': len(tasks),
            'task_ids': [task.id for task in tasks]
        }