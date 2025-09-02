"""
Collaboration service for team workspaces
Manages workspaces without authentication
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class CollaborationService:
    """Service for managing team collaboration workspaces"""
    
    def __init__(self, data_dir: str = 'workspace_data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.workspaces_file = self.data_dir / 'workspaces.json'
        self.load_workspaces()
    
    def load_workspaces(self):
        """Load workspaces from file"""
        if self.workspaces_file.exists():
            with open(self.workspaces_file, 'r') as f:
                self.workspaces = json.load(f)
        else:
            self.workspaces = {}
            self.save_workspaces()
    
    def save_workspaces(self):
        """Save workspaces to file"""
        with open(self.workspaces_file, 'w') as f:
            json.dump(self.workspaces, f, indent=2)
    
    def create_workspace(self, name: str, description: str = "") -> str:
        """Create a new workspace"""
        workspace_id = str(uuid.uuid4())[:8]
        workspace = {
            'id': workspace_id,
            'name': name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'tasks': {},
            'labels': [
                {'name': 'PERSON', 'color': '#FF6B6B'},
                {'name': 'LOCATION', 'color': '#4ECDC4'},
                {'name': 'ORGANIZATION', 'color': '#45B7D1'},
                {'name': 'DATE', 'color': '#96CEB4'},
                {'name': 'MISC', 'color': '#FFA500'}
            ],
            'members': [],
            'annotation_sessions': {}
        }
        
        self.workspaces[workspace_id] = workspace
        workspace_dir = self.data_dir / workspace_id
        workspace_dir.mkdir(exist_ok=True)
        self.save_workspaces()
        
        return workspace_id
    
    def get_workspace(self, workspace_id: str) -> Optional[Dict]:
        """Get workspace by ID"""
        return self.workspaces.get(workspace_id)
    
    def list_workspaces(self) -> List[Dict]:
        """List all workspaces"""
        return list(self.workspaces.values())
    
    def delete_workspace(self, workspace_id: str) -> bool:
        """Delete a workspace"""
        if workspace_id in self.workspaces:
            del self.workspaces[workspace_id]
            self.save_workspaces()
            
            # Delete workspace directory
            workspace_dir = self.data_dir / workspace_id
            if workspace_dir.exists():
                import shutil
                shutil.rmtree(workspace_dir)
            
            return True
        return False
    
    def add_task(self, workspace_id: str, text: str, metadata: Dict = None) -> Optional[str]:
        """Add a task to workspace with duplicate detection"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return None
        
        # Check for duplicate content using text hash
        import hashlib
        text_hash = hashlib.md5(text.strip().encode()).hexdigest()
        
        # Check if task with same content already exists
        for existing_task in workspace['tasks'].values():
            existing_hash = hashlib.md5(existing_task['text'].strip().encode()).hexdigest()
            if existing_hash == text_hash:
                return existing_task['id']  # Return existing task ID instead of creating duplicate
        
        # Create new task only if no duplicate found
        task_id = str(uuid.uuid4())[:8]
        task = {
            'id': task_id,
            'text': text,
            'created_at': datetime.now().isoformat(),
            'annotations': {},
            'status': 'pending',
            'metadata': metadata or {}
        }
        
        workspace['tasks'][task_id] = task
        self.save_workspaces()
        return task_id
    
    def get_task(self, workspace_id: str, task_id: str) -> Optional[Dict]:
        """Get specific task"""
        workspace = self.get_workspace(workspace_id)
        if workspace and task_id in workspace.get('tasks', {}):
            return workspace['tasks'][task_id]
        return None
    
    def update_task_status(self, workspace_id: str, task_id: str, status: str) -> bool:
        """Update task status"""
        workspace = self.get_workspace(workspace_id)
        if workspace and task_id in workspace.get('tasks', {}):
            workspace['tasks'][task_id]['status'] = status
            self.save_workspaces()
            return True
        return False
    
    def add_member_to_workspace(self, workspace_id: str, member_name: str) -> bool:
        """Add member to workspace"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False
        
        if member_name not in workspace.get('members', []):
            workspace.setdefault('members', []).append(member_name)
            self.save_workspaces()
        
        return True
    
    def add_annotation(self, workspace_id: str, task_id: str, member_name: str, 
                      annotations: List[Dict]) -> bool:
        """Add annotation from a team member"""
        workspace = self.get_workspace(workspace_id)
        if not workspace or task_id not in workspace['tasks']:
            return False
        
        task = workspace['tasks'][task_id]
        
        if 'annotations' not in task:
            task['annotations'] = {}
        
        # Store annotations by member with timestamp
        task['annotations'][member_name] = {
            'data': annotations,
            'timestamp': datetime.now().isoformat(),
            'version': len(task['annotations'].get(member_name, {}).get('history', [])) + 1
        }
        
        # Keep history of annotations
        if member_name not in task['annotations']:
            task['annotations'][member_name] = {'history': []}
        
        task['annotations'][member_name].setdefault('history', []).append({
            'data': annotations,
            'timestamp': datetime.now().isoformat()
        })
        
        self.save_workspaces()
        return True
    
    def merge_annotations(self, workspace_id: str, task_id: str, 
                         strategy: str = 'union') -> Optional[List[Dict]]:
        """
        Merge annotations from all team members
        Strategies:
        - union: Include all unique annotations
        - intersection: Only annotations agreed by all
        - majority: Annotations agreed by majority
        """
        workspace = self.get_workspace(workspace_id)
        if not workspace or task_id not in workspace['tasks']:
            return None
        
        task = workspace['tasks'][task_id]
        all_annotations = task.get('annotations', {})
        
        if not all_annotations:
            return []
        
        if strategy == 'union':
            return self._merge_union(all_annotations)
        elif strategy == 'intersection':
            return self._merge_intersection(all_annotations)
        elif strategy == 'majority':
            return self._merge_majority(all_annotations)
        else:
            return self._merge_union(all_annotations)
    
    def _merge_union(self, all_annotations: Dict) -> List[Dict]:
        """Merge strategy: Include all unique annotations"""
        merged = []
        seen = set()
        
        for member, annotation_data in all_annotations.items():
            for ann in annotation_data.get('data', []):
                ann_key = (ann['start'], ann['end'], ann['label'])
                if ann_key not in seen:
                    seen.add(ann_key)
                    ann['annotators'] = [member]
                    ann['confidence'] = 1 / len(all_annotations)
                    merged.append(ann)
                else:
                    # Find existing annotation and add member
                    for m in merged:
                        if (m['start'], m['end'], m['label']) == ann_key:
                            m['annotators'].append(member)
                            m['confidence'] = len(m['annotators']) / len(all_annotations)
                            break
        
        merged.sort(key=lambda x: x['start'])
        return merged
    
    def _merge_intersection(self, all_annotations: Dict) -> List[Dict]:
        """Merge strategy: Only annotations agreed by all members"""
        if not all_annotations:
            return []
        
        annotation_counts = {}
        total_members = len(all_annotations)
        
        for member, annotation_data in all_annotations.items():
            for ann in annotation_data.get('data', []):
                ann_key = (ann['start'], ann['end'], ann['label'])
                if ann_key not in annotation_counts:
                    annotation_counts[ann_key] = {
                        'annotation': ann,
                        'annotators': []
                    }
                annotation_counts[ann_key]['annotators'].append(member)
        
        # Only keep annotations agreed by all
        merged = []
        for ann_key, data in annotation_counts.items():
            if len(data['annotators']) == total_members:
                ann = data['annotation'].copy()
                ann['annotators'] = data['annotators']
                ann['confidence'] = 1.0
                merged.append(ann)
        
        merged.sort(key=lambda x: x['start'])
        return merged
    
    def _merge_majority(self, all_annotations: Dict) -> List[Dict]:
        """Merge strategy: Annotations agreed by majority"""
        if not all_annotations:
            return []
        
        annotation_counts = {}
        total_members = len(all_annotations)
        threshold = total_members / 2
        
        for member, annotation_data in all_annotations.items():
            for ann in annotation_data.get('data', []):
                ann_key = (ann['start'], ann['end'], ann['label'])
                if ann_key not in annotation_counts:
                    annotation_counts[ann_key] = {
                        'annotation': ann,
                        'annotators': []
                    }
                annotation_counts[ann_key]['annotators'].append(member)
        
        # Keep annotations agreed by majority
        merged = []
        for ann_key, data in annotation_counts.items():
            if len(data['annotators']) > threshold:
                ann = data['annotation'].copy()
                ann['annotators'] = data['annotators']
                ann['confidence'] = len(data['annotators']) / total_members
                merged.append(ann)
        
        merged.sort(key=lambda x: x['start'])
        return merged
    
    def export_workspace(self, workspace_id: str, merge_strategy: str = 'union') -> Optional[Dict]:
        """Export workspace with merged annotations"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return None
        
        export_data = {
            'workspace': {
                'id': workspace['id'],
                'name': workspace['name'],
                'description': workspace.get('description', ''),
                'created_at': workspace['created_at'],
                'members': workspace.get('members', []),
                'labels': workspace.get('labels', [])
            },
            'tasks': [],
            'export_date': datetime.now().isoformat(),
            'merge_strategy': merge_strategy
        }
        
        for task_id, task in workspace.get('tasks', {}).items():
            task_export = {
                'id': task_id,
                'text': task['text'],
                'created_at': task['created_at'],
                'status': task.get('status', 'pending'),
                'individual_annotations': task.get('annotations', {}),
                'merged_annotations': self.merge_annotations(workspace_id, task_id, merge_strategy)
            }
            export_data['tasks'].append(task_export)
        
        return export_data
    
    def get_statistics(self, workspace_id: str) -> Optional[Dict]:
        """Get workspace statistics"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return None
        
        stats = {
            'workspace_name': workspace['name'],
            'total_tasks': len(workspace.get('tasks', {})),
            'total_members': len(workspace.get('members', [])),
            'tasks_by_status': {},
            'annotations_by_member': {},
            'label_distribution': {}
        }
        
        # Count tasks by status
        for task in workspace.get('tasks', {}).values():
            status = task.get('status', 'pending')
            stats['tasks_by_status'][status] = stats['tasks_by_status'].get(status, 0) + 1
            
            # Count annotations by member
            for member in task.get('annotations', {}):
                stats['annotations_by_member'][member] = stats['annotations_by_member'].get(member, 0) + 1
        
        return stats