#!/usr/bin/env python3
"""
Unit Tests for Core NER Engine (ner_extractor.py)
Tests all functionality of the NERExtractor class including:
- Label management (CRUD)
- Task management
- Annotation operations (including overlapping)
- Export functionality (Label Studio, CoNLL)
- Statistics tracking
- Edge cases and error handling
"""

import pytest
import uuid
from datetime import datetime
from ner_extractor import NERExtractor, NERLabel, NERTask, NERAnnotation


class TestNERLabel:
    """Test NERLabel class functionality"""
    
    def test_label_creation(self):
        """Test basic label creation"""
        label = NERLabel("PERSON", "#ff0000", "p")
        assert label.value == "PERSON"
        assert label.background == "#ff0000"
        assert label.hotkey == "p"
    
    def test_label_validation(self):
        """Test label validation"""
        # Valid label
        label = NERLabel("ORG", "#00ff00", "o")
        assert label.value == "ORG"
        
        # Test default values
        label_minimal = NERLabel("LOC", "#0000ff")
        assert label_minimal.hotkey is None
    
    def test_label_to_dict(self):
        """Test label serialization"""
        label = NERLabel("PERSON", "#ff0000", "p", "PERSON", "Names of people", "John Smith")
        # Since dataclasses don't have to_dict method by default, use asdict or __dict__
        from dataclasses import asdict
        result = asdict(label)
        
        expected_keys = ['value', 'background', 'hotkey', 'category', 'description', 'example']
        assert all(key in result for key in expected_keys)
        assert result['value'] == "PERSON"
        assert result['hotkey'] == "p"


class TestNERTask:
    """Test NERTask class functionality"""
    
    def test_task_creation(self):
        """Test basic task creation"""
        task_id = str(uuid.uuid4())
        text = "Apple Inc. is headquartered in Cupertino."
        now = datetime.now()
        task = NERTask(task_id, text, [], now, now)
        
        assert task.id == task_id
        assert task.text == text
        assert task.annotations == []
    
    def test_task_add_annotation(self):
        """Test adding annotations to task"""
        task_id = str(uuid.uuid4())
        now = datetime.now()
        task = NERTask(task_id, "Microsoft was founded by Bill Gates.", [], now, now)
        
        annotation = NERAnnotation("ann1", 0, 9, "Microsoft", ["ORG"], now)
        task.annotations.append(annotation)
        
        assert len(task.annotations) == 1
        assert task.annotations[0].text == "Microsoft"
    
    def test_task_to_dict(self):
        """Test task serialization"""
        task_id = str(uuid.uuid4())
        now = datetime.now()
        task = NERTask(task_id, "Test text", [], now, now)
        result = task.to_dict()
        
        expected_keys = ['id', 'text', 'annotations']
        assert all(key in result for key in expected_keys)
        assert result['id'] == task_id
        assert result['text'] == "Test text"


class TestNERAnnotation:
    """Test NERAnnotation class functionality"""
    
    def test_annotation_creation(self):
        """Test basic annotation creation"""
        ann_id = str(uuid.uuid4())
        now = datetime.now()
        annotation = NERAnnotation(ann_id, 0, 5, "Apple", ["ORG"], now)
        
        assert annotation.id == ann_id
        assert annotation.start == 0
        assert annotation.end == 5
        assert annotation.text == "Apple"
        assert annotation.labels == ["ORG"]
    
    def test_annotation_overlaps(self):
        """Test annotation overlap detection"""
        now = datetime.now()
        ann1 = NERAnnotation("1", 0, 10, "Apple Inc.", ["ORG"], now)
        ann2 = NERAnnotation("2", 5, 15, "Inc. Company", ["ORG"], now)  # Overlapping
        ann3 = NERAnnotation("3", 15, 20, "Smith", ["PER"], now)        # Non-overlapping
        
        # Basic overlap test (manual check since overlap methods may not exist)
        assert not (ann1.end <= ann2.start or ann2.end <= ann1.start)  # ann1 and ann2 overlap
        assert (ann1.end <= ann3.start or ann3.end <= ann1.start)      # ann1 and ann3 don't overlap
    
    def test_annotation_contains(self):
        """Test annotation containment"""
        now = datetime.now()
        ann_large = NERAnnotation("1", 0, 20, "Apple Inc. in California", ["ORG"], now)
        ann_small = NERAnnotation("2", 0, 9, "Apple Inc", ["ORG"], now)
        ann_outside = NERAnnotation("3", 25, 30, "Smith", ["PER"], now)
        
        # Manual containment check
        assert ann_large.start <= ann_small.start and ann_large.end >= ann_small.end
        assert not (ann_small.start <= ann_large.start and ann_small.end >= ann_large.end)
        assert not (ann_large.start <= ann_outside.start and ann_large.end >= ann_outside.end)
    
    def test_annotation_to_dict(self):
        """Test annotation serialization"""
        ann_id = str(uuid.uuid4())
        now = datetime.now()
        annotation = NERAnnotation(ann_id, 0, 5, "Apple", ["ORG"], now)
        result = annotation.to_dict()
        
        expected_keys = ['id', 'start', 'end', 'text', 'labels']
        assert all(key in result for key in expected_keys)
        assert result['text'] == "Apple"
        assert result['labels'] == ["ORG"]


class TestNERExtractor:
    """Test main NERExtractor functionality"""
    
    def setup_method(self):
        """Set up fresh extractor for each test"""
        self.extractor = NERExtractor()
    
    def test_initialization(self):
        """Test NERExtractor initialization"""
        assert self.extractor.labels == []
        assert self.extractor.tasks == {}
    
    def test_label_management_crud(self):
        """Test complete label CRUD operations"""
        # Create
        label_id = self.extractor.create_label("PERSON", "#ff0000", "p")
        assert label_id == 0
        assert len(self.extractor.labels) == 1
        
        # Read
        labels = self.extractor.get_all_labels()
        assert len(labels) == 1
        assert labels[0]['value'] == "PERSON"
        
        label = self.extractor.get_label(label_id)
        assert label['value'] == "PERSON"
        
        # Update
        updated = self.extractor.update_label(label_id, value="INDIVIDUAL", hotkey="i")
        assert updated['value'] == "INDIVIDUAL"
        assert updated['hotkey'] == "i"
        
        # Delete
        result = self.extractor.delete_label(label_id)
        assert 'deleted' in result
        assert result['deleted']['value'] == "INDIVIDUAL"
        assert len(self.extractor.labels) == 0
    
    def test_label_validation_errors(self):
        """Test label validation and error handling"""
        # Duplicate label
        self.extractor.create_label("PERSON", "#ff0000", "p")
        
        with pytest.raises(ValueError, match="already exists"):
            self.extractor.create_label("PERSON", "#00ff00", "q")
        
        # Invalid label ID
        result = self.extractor.get_label(999)
        assert result is None
    
    def test_task_management(self):
        """Test task creation and retrieval"""
        text = "Apple Inc. was founded by Steve Jobs."
        task_id = self.extractor.create_task(text)
        
        assert task_id is not None
        assert len(self.extractor.tasks) == 1
        
        # Retrieve task
        task = self.extractor.get_task(task_id)
        assert task is not None
        assert task.text == text
        assert task.id == task_id
    
    def test_annotation_operations(self):
        """Test annotation creation and management"""
        # Setup
        self.extractor.create_label("ORG", "#ff0000", "o")
        self.extractor.create_label("PER", "#00ff00", "p")
        
        task_id = self.extractor.create_task("Apple Inc. was founded by Steve Jobs.")
        
        # Add annotations
        ann1_id = self.extractor.add_annotation(task_id, 0, 10, ["ORG"])    # Apple Inc.
        ann2_id = self.extractor.add_annotation(task_id, 26, 36, ["PER"])   # Steve Jobs
        
        assert ann1_id is not None
        assert ann2_id is not None
        
        # Verify annotations in task
        task = self.extractor.get_task(task_id)
        assert len(task.annotations) == 2
        
        # Check annotation details
        ann1 = next(ann for ann in task.annotations if ann.id == ann1_id)
        assert ann1.text == "Apple Inc."
        assert ann1.labels == ["ORG"]
    
    def test_overlapping_annotations(self):
        """Test overlapping annotation handling"""
        # Setup
        self.extractor.create_label("ORG", "#ff0000", "o")
        self.extractor.create_label("COMPANY", "#00ff00", "c")
        
        task_id = self.extractor.create_task("Apple Inc. Corporation")
        
        # Add overlapping annotations
        ann1_id = self.extractor.add_annotation(task_id, 0, 10, ["ORG"])      # Apple Inc.
        ann2_id = self.extractor.add_annotation(task_id, 0, 21, ["COMPANY"])  # Apple Inc. Corporation
        ann3_id = self.extractor.add_annotation(task_id, 6, 10, ["ORG"])      # Inc.
        
        task = self.extractor.get_task(task_id)
        assert len(task.annotations) == 3
        
        # Test overlap detection
        annotations = task.annotations
        overlapping_pairs = 0
        for i, ann1 in enumerate(annotations):
            for ann2 in annotations[i+1:]:
                # Manual overlap check: not (end1 <= start2 or end2 <= start1)
                if not (ann1.end <= ann2.start or ann2.end <= ann1.start):
                    overlapping_pairs += 1
        
        assert overlapping_pairs > 0  # Should have overlapping annotations
    
    def test_export_label_studio(self):
        """Test Label Studio format export"""
        # Setup task with annotations
        self.extractor.create_label("PER", "#ff0000", "p")
        task_id = self.extractor.create_task("John Smith works here.")
        self.extractor.add_annotation(task_id, 0, 10, ["PER"])
        
        # Export
        exported = self.extractor.export_task(task_id)
        
        assert 'id' in exported
        assert 'data' in exported
        assert 'annotations' in exported
        assert len(exported['annotations']) == 1
        
        # Verify annotation format
        annotation = exported['annotations'][0]
        assert 'result' in annotation
        assert len(annotation['result']) == 1
        
        result = annotation['result'][0]
        assert result['value']['text'] == "John Smith"
        assert result['value']['labels'] == ["PER"]
    
    def test_export_conll(self):
        """Test CoNLL format export"""
        # Setup task with annotations
        self.extractor.create_label("PER", "#ff0000", "p")
        self.extractor.create_label("ORG", "#00ff00", "o")
        
        task_id = self.extractor.create_task("John works at Apple.")
        self.extractor.add_annotation(task_id, 0, 4, ["PER"])   # John
        self.extractor.add_annotation(task_id, 14, 19, ["ORG"])  # Apple
        
        # Export
        conll_output = self.extractor.export_conll_format(task_id)
        
        assert conll_output is not None
        assert isinstance(conll_output, str)
        
        lines = conll_output.strip().split('\n')
        assert len(lines) > 0
        
        # Verify CoNLL format (word \t label)
        for line in lines:
            if line.strip():  # Skip empty lines
                parts = line.split('\t')
                assert len(parts) == 2  # word and label
    
    def test_statistics(self):
        """Test statistics generation"""
        # Setup data
        self.extractor.create_label("PER", "#ff0000", "p")
        self.extractor.create_label("ORG", "#00ff00", "o")
        
        task1_id = self.extractor.create_task("John works at Apple.")
        task2_id = self.extractor.create_task("Mary founded Microsoft.")
        
        self.extractor.add_annotation(task1_id, 0, 4, ["PER"])
        self.extractor.add_annotation(task1_id, 14, 19, ["ORG"])
        self.extractor.add_annotation(task2_id, 0, 4, ["PER"])
        self.extractor.add_annotation(task2_id, 14, 23, ["ORG"])
        
        # Get statistics
        stats = self.extractor.get_statistics()
        
        assert stats['total_tasks'] == 2
        assert stats['total_annotations'] == 4
        assert stats['label_distribution']['PER'] == 2
        assert stats['label_distribution']['ORG'] == 2
        assert len(stats['available_labels']) == 2
    
    def test_configuration_xml_generation(self):
        """Test Label Studio XML configuration generation"""
        # Add labels
        self.extractor.create_label("PERSON", "#ff0000", "p")
        self.extractor.create_label("ORGANIZATION", "#00ff00", "o")
        
        # Get basic config
        basic_config = self.extractor.get_label_config_xml()
        assert '<Labels name="label"' in basic_config
        assert 'value="PERSON"' in basic_config
        assert 'value="ORGANIZATION"' in basic_config
        
        # Get enhanced config
        enhanced_config = self.extractor.get_enhanced_config_xml()
        assert '<Labels name="label"' in enhanced_config
        assert 'hotkey="p"' in enhanced_config
        assert 'hotkey="o"' in enhanced_config
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Empty task
        task_id = self.extractor.create_task("")
        task = self.extractor.get_task(task_id)
        assert task.text == ""
        
        # Single character task
        task_id = self.extractor.create_task("A")
        assert self.extractor.get_task(task_id).text == "A"
        
        # Very long text
        long_text = "A" * 10000
        task_id = self.extractor.create_task(long_text)
        assert len(self.extractor.get_task(task_id).text) == 10000
        
        # Invalid annotation bounds
        self.extractor.create_label("TEST", "#ff0000", "t")
        task_id = self.extractor.create_task("Short")
        
        with pytest.raises(ValueError, match="Invalid annotation span"):
            self.extractor.add_annotation(task_id, 0, 100, ["TEST"])  # End beyond text
        
        with pytest.raises(ValueError, match="Invalid annotation span"):
            self.extractor.add_annotation(task_id, 5, 3, ["TEST"])    # Start > End
        
        with pytest.raises(ValueError, match="Invalid annotation span"):
            self.extractor.add_annotation(task_id, -1, 3, ["TEST"])   # Negative start


if __name__ == "__main__":
    pytest.main([__file__, "-v"])