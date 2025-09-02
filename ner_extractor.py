#!/usr/bin/env python3
"""
Label Studio NER Extractor
Standalone Named Entity Recognition interface extracted from Label Studio
"""

import json
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NERLabel:
    """Named Entity Recognition label definition"""
    value: str
    background: str
    hotkey: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    example: Optional[str] = None


@dataclass
class NERAnnotation:
    """NER annotation for a text span"""
    id: str
    start: int
    end: int
    text: str
    labels: List[str]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'start': self.start,
            'end': self.end,
            'text': self.text,
            'labels': self.labels,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class NERTask:
    """NER annotation task"""
    id: str
    text: str
    annotations: List[NERAnnotation]
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'text': self.text,
            'annotations': [ann.to_dict() for ann in self.annotations],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class NERExtractor:
    """Named Entity Recognition functionality extracted from Label Studio"""
    
    # Default NER labels - empty by default, loaded from files or manually added
    DEFAULT_LABELS = [
        # Labels will be loaded dynamically from uploaded files or added manually
    ]
    
    def __init__(self, labels: Optional[List[NERLabel]] = None):
        self.labels = labels or list(self.DEFAULT_LABELS)  # Create new list instance
        self.tasks: Dict[str, NERTask] = {}
    
    def get_label_config_xml(self) -> str:
        """Generate Label Studio compatible XML configuration"""
        labels_xml = []
        for label in self.labels:
            hotkey_attr = f' hotkey="{label.hotkey}"' if label.hotkey else ''
            labels_xml.append(f'    <Label value="{label.value}" background="{label.background}"{hotkey_attr}/>')
        
        return f"""<View>
  <Labels name="label" toName="text">
{chr(10).join(labels_xml)}
  </Labels>
  <Text name="text" value="$text"/>
</View>"""
    
    def get_enhanced_config_xml(self) -> str:
        """Generate enhanced XML configuration with filtering and word alignment"""
        labels_xml = []
        for label in self.labels:
            hotkey_attr = f' hotkey="{label.hotkey}"' if label.hotkey else ''
            labels_xml.append(f'    <Label value="{label.value}" background="{label.background}"{hotkey_attr}/>')
        
        return f"""<View>
  <Filter name="filter" toName="label" hotkey="shift+f" minlength="1" />
  <Labels name="label" toName="text" showInline="false">
{chr(10).join(labels_xml)}
  </Labels>
  <Text name="text" value="$text" granularity="word"/>
  <Choices name="confidence" toName="text" perRegion="true">
    <Choice value="High" />
    <Choice value="Medium" />
    <Choice value="Low" />
  </Choices>
</View>"""
    
    def create_task(self, text: str, task_id: Optional[str] = None) -> str:
        """Create a new NER annotation task"""
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        now = datetime.now()
        task = NERTask(
            id=task_id,
            text=text,
            annotations=[],
            created_at=now,
            updated_at=now
        )
        
        self.tasks[task_id] = task
        return task_id
    
    def add_annotation(self, task_id: str, start: int, end: int, labels: List[str]) -> str:
        """Add an annotation to a task with overlap support"""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        
        # Validate bounds
        if end > len(task.text) or start < 0 or start >= end:
            raise ValueError(f"Invalid annotation span: start={start}, end={end}, text_length={len(task.text)}")
        
        # Check for exact duplicates
        text_span = task.text[start:end]
        for existing in task.annotations:
            if existing.start == start and existing.end == end and existing.labels == labels:
                return existing.id  # Return existing annotation ID
        
        annotation_id = str(uuid.uuid4())
        annotation = NERAnnotation(
            id=annotation_id,
            start=start,
            end=end,
            text=text_span,
            labels=labels,
            created_at=datetime.now()
        )
        
        task.annotations.append(annotation)
        task.updated_at = datetime.now()
        
        # Log overlapping annotations for debugging
        overlapping = [ann for ann in task.annotations 
                      if ann.id != annotation_id and 
                      not (ann.end <= start or ann.start >= end)]
        
        if overlapping:
            print(f"Added overlapping annotation: {text_span} ({start}-{end}) overlaps with {len(overlapping)} existing annotations")
        
        return annotation_id
    
    def get_task(self, task_id: str) -> Optional[NERTask]:
        """Get a task by ID"""
        return self.tasks.get(task_id)
    
    def export_task(self, task_id: str) -> Dict[str, Any]:
        """Export task in Label Studio format"""
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Convert to Label Studio format
        return {
            'id': int(task.id.replace('-', '')[:8], 16),  # Convert UUID to int
            'data': {'text': task.text},
            'annotations': [{
                'id': int(ann.id.replace('-', '')[:8], 16),
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
            } for ann in task.annotations],
            'predictions': []
        }
    
    def import_label_studio_task(self, ls_task: Dict[str, Any]) -> str:
        """Import task from Label Studio format"""
        data = ls_task.get('data', {})
        text = data.get('text', '')
        
        task_id = self.create_task(text)
        
        # Import annotations
        annotations = ls_task.get('annotations', [])
        for ann in annotations:
            for result in ann.get('result', []):
                if result.get('type') == 'labels':
                    value = result.get('value', {})
                    self.add_annotation(
                        task_id,
                        value.get('start', 0),
                        value.get('end', 0),
                        value.get('labels', [])
                    )
        
        return task_id
    
    def export_conll_format(self, task_id: str) -> str:
        """Export annotations in CoNLL-2003 format"""
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Create token-level annotations
        tokens = task.text.split()
        token_labels = ['O'] * len(tokens)
        
        current_pos = 0
        for token_idx, token in enumerate(tokens):
            token_start = task.text.find(token, current_pos)
            token_end = token_start + len(token)
            
            # Check if token overlaps with any annotation
            for ann in task.annotations:
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
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get annotation statistics"""
        total_tasks = len(self.tasks)
        total_annotations = sum(len(task.annotations) for task in self.tasks.values())
        
        label_counts = {}
        for task in self.tasks.values():
            for ann in task.annotations:
                for label in ann.labels:
                    label_counts[label] = label_counts.get(label, 0) + 1
        
        return {
            'total_tasks': total_tasks,
            'total_annotations': total_annotations,
            'label_distribution': label_counts,
            'available_labels': [label.value for label in self.labels]
        }

    def create_label(self, value, background="#999999", hotkey=None, category=None, description=None, example=None):
        """Create a new label"""
        # Check if label already exists
        for label in self.labels:
            if label.value == value:
                raise ValueError(f"Label '{value}' already exists")
        
        new_label = NERLabel(value, background, hotkey, category, description, example)
        self.labels.append(new_label)
        return len(self.labels) - 1  # Return index as ID

    def get_all_labels(self):
        """Get all labels"""
        return [{'id': i, 'value': label.value, 'background': label.background, 'hotkey': label.hotkey,
                 'category': label.category, 'description': label.description, 'example': label.example} 
                for i, label in enumerate(self.labels)]

    def get_label(self, label_id):
        """Get label by ID (supports both integer index and string value)"""
        # If it's a string, try to find by value first
        if isinstance(label_id, str):
            for i, label in enumerate(self.labels):
                if label.value == label_id:
                    return {'id': i, 'value': label.value, 'background': label.background, 'hotkey': label.hotkey,
                           'category': label.category, 'description': label.description, 'example': label.example}
            # If not found by value, try to convert to int
            try:
                label_id = int(label_id)
            except (ValueError, TypeError):
                return None
        
        # Handle as integer ID
        if isinstance(label_id, int) and 0 <= label_id < len(self.labels):
            label = self.labels[label_id]
            return {'id': label_id, 'value': label.value, 'background': label.background, 'hotkey': label.hotkey,
                   'category': label.category, 'description': label.description, 'example': label.example}
        return None

    def update_label(self, label_id, value=None, background=None, hotkey=None, category=None, description=None, example=None):
        """Update an existing label (supports both integer index and string value)"""
        actual_id = label_id
        
        # If it's a string, try to find by value first
        if isinstance(label_id, str):
            for i, label in enumerate(self.labels):
                if label.value == label_id:
                    actual_id = i
                    break
            else:
                # If not found by value, try to convert to int
                try:
                    actual_id = int(label_id)
                except (ValueError, TypeError):
                    raise ValueError(f"Label '{label_id}' not found")
        
        # Validate ID bounds
        if not isinstance(actual_id, int) or actual_id < 0 or actual_id >= len(self.labels):
            raise ValueError(f"Label ID {label_id} not found")
        
        label = self.labels[actual_id]
        
        # Check for duplicate names if updating value
        if value and value != label.value:
            for i, existing_label in enumerate(self.labels):
                if i != actual_id and existing_label.value == value:
                    raise ValueError(f"Label '{value}' already exists")
        
        # Update fields
        if value is not None:
            label.value = value
        if background is not None:
            label.background = background
        if hotkey is not None:
            label.hotkey = hotkey
        if category is not None:
            label.category = category
        if description is not None:
            label.description = description
        if example is not None:
            label.example = example
            
        return {'id': actual_id, 'value': label.value, 'background': label.background, 'hotkey': label.hotkey,
                'category': label.category, 'description': label.description, 'example': label.example}

    def delete_label(self, label_id):
        """Delete a label (supports both integer index and string value)"""
        actual_id = label_id
        
        # If it's a string, try to find by value first
        if isinstance(label_id, str):
            for i, label in enumerate(self.labels):
                if label.value == label_id:
                    actual_id = i
                    break
            else:
                # If not found by value, try to convert to int
                try:
                    actual_id = int(label_id)
                except (ValueError, TypeError):
                    raise ValueError(f"Label '{label_id}' not found")
        
        # Validate ID bounds
        if not isinstance(actual_id, int) or actual_id < 0 or actual_id >= len(self.labels):
            raise ValueError(f"Label ID {label_id} not found")
        
        deleted_label = self.labels.pop(actual_id)
        
        # Update annotations that used this label
        # Note: This is a simplified approach - in practice you might want to handle this differently
        for task in self.tasks.values():
            annotations_to_remove = []
            for i, annotation in enumerate(task.annotations):
                # Remove annotations that only had this label
                if len(annotation.labels) == 1 and annotation.labels[0] == deleted_label.value:
                    annotations_to_remove.append(i)
                # Remove this label from multi-label annotations
                elif deleted_label.value in annotation.labels:
                    annotation.labels.remove(deleted_label.value)
            
            # Remove annotations in reverse order to maintain indices
            for i in reversed(annotations_to_remove):
                task.annotations.pop(i)
        
        return {'deleted': {'value': deleted_label.value, 'background': deleted_label.background, 'hotkey': deleted_label.hotkey}}


if __name__ == "__main__":
    # Example usage
    extractor = NERExtractor()
    
    # Create a sample task
    sample_text = "John Smith works at Microsoft in Seattle. He previously worked at Google in Mountain View."
    task_id = extractor.create_task(sample_text)
    
    # Add annotations
    extractor.add_annotation(task_id, 0, 10, ["PER"])        # John Smith
    extractor.add_annotation(task_id, 20, 29, ["ORG"])       # Microsoft
    extractor.add_annotation(task_id, 33, 40, ["LOC"])       # Seattle
    extractor.add_annotation(task_id, 65, 71, ["ORG"])       # Google
    extractor.add_annotation(task_id, 75, 88, ["LOC"])       # Mountain View
    
    # Print configuration
    print("Label Studio XML Configuration:")
    print(extractor.get_label_config_xml())
    print("\nEnhanced XML Configuration:")
    print(extractor.get_enhanced_config_xml())
    
    # Export task
    print("\nExported Task:")
    print(json.dumps(extractor.export_task(task_id), indent=2))
    
    # Export CoNLL format
    print("\nCoNLL Format:")
    print(extractor.export_conll_format(task_id))
    
    # Statistics
    print("\nStatistics:")
    print(json.dumps(extractor.get_statistics(), indent=2))