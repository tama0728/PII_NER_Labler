"""
Label repository implementation
Specialized data access for label management
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import func
from backend.models.label import Label
from backend.repositories.base_repository import BaseRepository

class LabelRepository(BaseRepository[Label]):
    """Repository for label-specific database operations"""
    
    def __init__(self):
        super().__init__(Label)
    
    def get_labels_by_project(self, project_id: int, active_only: bool = True) -> List[Label]:
        """Get labels for a specific project"""
        query = self.session.query(Label).filter(Label.project_id == project_id)
        
        if active_only:
            query = query.filter(Label.is_active == True)
        
        return query.order_by(Label.sort_order, Label.value).all()
    
    def get_label_by_value(self, project_id: int, value: str) -> Optional[Label]:
        """Get label by value within a project"""
        return self.session.query(Label).filter(
            Label.project_id == project_id,
            Label.value == value
        ).first()
    
    def create_project_label(self, project_id: int, value: str, 
                           background: str = '#999999',
                           hotkey: str = None,
                           category: str = None,
                           description: str = None,
                           example: str = None) -> Label:
        """Create a new label for a project"""
        # Check if label already exists in this project
        existing = self.get_label_by_value(project_id, value)
        if existing:
            raise ValueError(f"Label '{value}' already exists in this project")
        
        # Check if hotkey is already used in this project
        if hotkey:
            existing_hotkey = self.session.query(Label).filter(
                Label.project_id == project_id,
                Label.hotkey == hotkey,
                Label.is_active == True
            ).first()
            if existing_hotkey:
                raise ValueError(f"Hotkey '{hotkey}' is already used by label '{existing_hotkey.value}'")
        
        # Get next sort order
        max_sort = self.session.query(func.max(Label.sort_order)).filter(
            Label.project_id == project_id
        ).scalar()
        sort_order = (max_sort or 0) + 1
        
        label = self.create(
            project_id=project_id,
            value=value,
            background=background,
            hotkey=hotkey,
            category=category,
            description=description,
            example=example,
            sort_order=sort_order
        )
        
        return label
    
    def update_label_order(self, label_id: int, new_sort_order: int) -> bool:
        """Update the sort order of a label"""
        label = self.get_by_id(label_id)
        if not label:
            return False
        
        # Get labels in the same project
        project_labels = self.get_labels_by_project(label.project_id, active_only=False)
        
        # Reorder labels
        old_order = label.sort_order
        if new_sort_order > old_order:
            # Moving down
            for other_label in project_labels:
                if old_order < other_label.sort_order <= new_sort_order:
                    other_label.sort_order -= 1
        else:
            # Moving up
            for other_label in project_labels:
                if new_sort_order <= other_label.sort_order < old_order:
                    other_label.sort_order += 1
        
        label.sort_order = new_sort_order
        self.session.commit()
        return True
    
    def get_available_hotkeys(self, project_id: int) -> List[str]:
        """Get list of available hotkeys for a project"""
        used_hotkeys = set()
        labels = self.get_labels_by_project(project_id, active_only=True)
        
        for label in labels:
            if label.hotkey:
                used_hotkeys.add(label.hotkey)
        
        # Standard hotkey options
        all_hotkeys = [str(i) for i in range(1, 10)] + list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        available = [hk for hk in all_hotkeys if hk not in used_hotkeys]
        
        return available
    
    def suggest_next_hotkey(self, project_id: int) -> Optional[str]:
        """Suggest the next available hotkey"""
        available = self.get_available_hotkeys(project_id)
        return available[0] if available else None
    
    def get_label_usage_statistics(self, project_id: int) -> List[Dict[str, Any]]:
        """Get usage statistics for all labels in a project"""
        labels = self.get_labels_by_project(project_id, active_only=False)
        statistics = []
        
        for label in labels:
            usage_count = label.get_usage_count()
            statistics.append({
                'label': label.to_dict(),
                'usage_count': usage_count,
                'can_be_deleted': label.can_be_deleted()
            })
        
        return sorted(statistics, key=lambda x: x['usage_count'], reverse=True)
    
    def deactivate_label(self, label_id: int) -> bool:
        """Deactivate a label (soft delete)"""
        label = self.get_by_id(label_id)
        if label:
            label.deactivate()
            return True
        return False
    
    def activate_label(self, label_id: int) -> bool:
        """Activate a label"""
        label = self.get_by_id(label_id)
        if label:
            label.activate()
            return True
        return False
    
    def duplicate_labels_to_project(self, source_project_id: int, 
                                  target_project_id: int) -> List[Label]:
        """Duplicate all labels from one project to another"""
        source_labels = self.get_labels_by_project(source_project_id, active_only=False)
        created_labels = []
        
        for source_label in source_labels:
            try:
                new_label = self.create_project_label(
                    project_id=target_project_id,
                    value=source_label.value,
                    background=source_label.background,
                    hotkey=source_label.hotkey,
                    category=source_label.category,
                    description=source_label.description,
                    example=source_label.example
                )
                created_labels.append(new_label)
            except ValueError:
                # Skip if label already exists
                continue
        
        return created_labels
    
    def import_labels_from_config(self, project_id: int, 
                                labels_config: List[Dict[str, Any]]) -> List[Label]:
        """Import labels from configuration data"""
        created_labels = []
        
        for i, label_config in enumerate(labels_config):
            try:
                label = self.create(
                    project_id=project_id,
                    value=label_config['value'],
                    background=label_config.get('background', '#999999'),
                    hotkey=label_config.get('hotkey'),
                    category=label_config.get('category'),
                    description=label_config.get('description'),
                    example=label_config.get('example'),
                    sort_order=i,
                    is_active=label_config.get('is_active', True)
                )
                created_labels.append(label)
            except Exception as e:
                # Log error but continue with other labels
                print(f"Failed to create label {label_config.get('value', 'unknown')}: {e}")
                continue
        
        return created_labels
    
    def export_labels_config(self, project_id: int) -> List[Dict[str, Any]]:
        """Export labels configuration for a project"""
        labels = self.get_labels_by_project(project_id, active_only=False)
        
        return [
            {
                'value': label.value,
                'background': label.background,
                'hotkey': label.hotkey,
                'category': label.category,
                'description': label.description,
                'example': label.example,
                'is_active': label.is_active,
                'sort_order': label.sort_order
            }
            for label in labels
        ]
    
    def get_label_conflicts(self, project_id: int) -> Dict[str, Any]:
        """Check for label conflicts (duplicate values, hotkeys, etc.)"""
        labels = self.get_labels_by_project(project_id, active_only=False)
        
        conflicts = {
            'duplicate_values': [],
            'duplicate_hotkeys': [],
            'invalid_colors': [],
            'missing_hotkeys': []
        }
        
        # Check for duplicate values
        value_counts = {}
        for label in labels:
            value_counts[label.value] = value_counts.get(label.value, 0) + 1
        
        conflicts['duplicate_values'] = [
            {'value': value, 'count': count}
            for value, count in value_counts.items() if count > 1
        ]
        
        # Check for duplicate hotkeys
        hotkey_labels = {}
        for label in labels:
            if label.hotkey and label.is_active:
                if label.hotkey not in hotkey_labels:
                    hotkey_labels[label.hotkey] = []
                hotkey_labels[label.hotkey].append(label.value)
        
        conflicts['duplicate_hotkeys'] = [
            {'hotkey': hotkey, 'labels': label_values}
            for hotkey, label_values in hotkey_labels.items() if len(label_values) > 1
        ]
        
        # Check for invalid colors
        for label in labels:
            if not label.validate_color(label.background):
                conflicts['invalid_colors'].append({
                    'label': label.value,
                    'color': label.background
                })
        
        # Check for missing hotkeys on active labels
        active_labels_without_hotkeys = [
            label.value for label in labels 
            if label.is_active and not label.hotkey
        ]
        conflicts['missing_hotkeys'] = active_labels_without_hotkeys
        
        return conflicts
    
    def fix_label_sort_orders(self, project_id: int) -> bool:
        """Fix and normalize sort orders for project labels"""
        labels = self.session.query(Label).filter(
            Label.project_id == project_id
        ).order_by(Label.sort_order, Label.value).all()
        
        for i, label in enumerate(labels):
            label.sort_order = i
        
        self.session.commit()
        return True
    
    def get_labels_by_category(self, project_id: int, category: str) -> List[Label]:
        """Get labels by category"""
        return self.session.query(Label).filter(
            Label.project_id == project_id,
            Label.category == category,
            Label.is_active == True
        ).order_by(Label.sort_order).all()
    
    def get_label_categories(self, project_id: int) -> List[str]:
        """Get unique label categories for a project"""
        categories = self.session.query(Label.category).filter(
            Label.project_id == project_id,
            Label.category.isnot(None),
            Label.is_active == True
        ).distinct().all()
        
        return [cat[0] for cat in categories if cat[0]]