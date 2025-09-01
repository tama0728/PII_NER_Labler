#!/usr/bin/env python3
"""
Integration Tests for Flask API Endpoints (app.py)
Tests all REST API endpoints including:
- NER task management (/api/ner/tasks)
- Annotation operations (/api/ner/tasks/{id}/annotations)
- Label/Tag management (/api/ner/tags)
- Export functionality (/api/ner/tasks/{id}/export, /api/ner/tasks/{id}/conll)
- Statistics (/api/ner/statistics)
- Configuration (/api/ner/config)
- File operations (/api/save-*)
- Authentication and error handling
"""

import pytest
import json
from app import create_app
from backend.database import db
from backend.config import Config


class TestConfig(Config):
    """Test configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


@pytest.fixture
def app():
    """Create and configure test app"""
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


class TestNERTaskAPI:
    """Test NER task management endpoints"""
    
    def test_create_task(self, client):
        """Test POST /api/ner/tasks - Create new task"""
        task_data = {
            'text': 'Apple Inc. was founded by Steve Jobs in Cupertino, California.'
        }
        
        response = client.post('/api/ner/tasks',
                             data=json.dumps(task_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'task_id' in data
        assert data['text'] == task_data['text']
    
    def test_create_task_empty_text(self, client):
        """Test task creation with empty text"""
        task_data = {'text': ''}
        
        response = client.post('/api/ner/tasks',
                             data=json.dumps(task_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_create_task_no_text(self, client):
        """Test task creation without text field"""
        task_data = {'other_field': 'value'}
        
        response = client.post('/api/ner/tasks',
                             data=json.dumps(task_data),
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_get_task(self, client):
        """Test GET /api/ner/tasks/{task_id} - Retrieve task"""
        # Create task first
        task_data = {'text': 'Microsoft Corporation is based in Redmond.'}
        response = client.post('/api/ner/tasks',
                             data=json.dumps(task_data),
                             content_type='application/json')
        
        task_id = response.get_json()['task_id']
        
        # Get task
        response = client.get(f'/api/ner/tasks/{task_id}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['text'] == task_data['text']
        assert data['id'] == task_id
    
    def test_get_nonexistent_task(self, client):
        """Test retrieving non-existent task"""
        response = client.get('/api/ner/tasks/nonexistent-id')
        assert response.status_code == 404
        
        data = response.get_json()
        assert 'error' in data


class TestAnnotationAPI:
    """Test annotation management endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_task(self, client):
        """Setup task for annotation tests"""
        task_data = {'text': 'Google was founded by Larry Page and Sergey Brin.'}
        response = client.post('/api/ner/tasks',
                             data=json.dumps(task_data),
                             content_type='application/json')
        self.task_id = response.get_json()['task_id']
        self.text = task_data['text']
    
    def test_add_annotation(self, client):
        """Test POST /api/ner/tasks/{task_id}/annotations - Add annotation"""
        annotation_data = {
            'start': 0,
            'end': 6,
            'labels': ['ORG']
        }
        
        response = client.post(f'/api/ner/tasks/{self.task_id}/annotations',
                             data=json.dumps(annotation_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'annotation_id' in data
    
    def test_add_multiple_annotations(self, client):
        """Test adding multiple annotations"""
        annotations = [
            {'start': 0, 'end': 6, 'labels': ['ORG']},      # Google
            {'start': 21, 'end': 31, 'labels': ['PER']},    # Larry Page
            {'start': 36, 'end': 47, 'labels': ['PER']},    # Sergey Brin
        ]
        
        annotation_ids = []
        for ann_data in annotations:
            response = client.post(f'/api/ner/tasks/{self.task_id}/annotations',
                                 data=json.dumps(ann_data),
                                 content_type='application/json')
            assert response.status_code == 200
            annotation_ids.append(response.get_json()['annotation_id'])
        
        assert len(annotation_ids) == 3
        assert len(set(annotation_ids)) == 3  # All unique IDs
    
    def test_add_overlapping_annotations(self, client):
        """Test adding overlapping annotations"""
        # First annotation
        ann1 = {'start': 0, 'end': 6, 'labels': ['ORG']}      # Google
        response1 = client.post(f'/api/ner/tasks/{self.task_id}/annotations',
                              data=json.dumps(ann1),
                              content_type='application/json')
        assert response1.status_code == 200
        
        # Overlapping annotation
        ann2 = {'start': 0, 'end': 15, 'labels': ['COMPANY']}   # Google was founded
        response2 = client.post(f'/api/ner/tasks/{self.task_id}/annotations',
                              data=json.dumps(ann2),
                              content_type='application/json')
        assert response2.status_code == 200
    
    def test_add_invalid_annotation(self, client):
        """Test adding annotation with invalid bounds"""
        invalid_annotations = [
            {'start': -1, 'end': 5, 'labels': ['ORG']},      # Negative start
            {'start': 0, 'end': 1000, 'labels': ['ORG']},    # End beyond text
            {'start': 10, 'end': 5, 'labels': ['ORG']},      # Start > end
            {'start': 0, 'end': 0, 'labels': ['ORG']},       # Zero length
        ]
        
        for ann_data in invalid_annotations:
            response = client.post(f'/api/ner/tasks/{self.task_id}/annotations',
                                 data=json.dumps(ann_data),
                                 content_type='application/json')
            assert response.status_code == 400
    
    def test_add_annotation_missing_fields(self, client):
        """Test adding annotation with missing fields"""
        incomplete_annotations = [
            {'end': 5, 'labels': ['ORG']},           # Missing start
            {'start': 0, 'labels': ['ORG']},         # Missing end
            {'start': 0, 'end': 5},                  # Missing labels
        ]
        
        for ann_data in incomplete_annotations:
            response = client.post(f'/api/ner/tasks/{self.task_id}/annotations',
                                 data=json.dumps(ann_data),
                                 content_type='application/json')
            assert response.status_code == 400


class TestLabelAPI:
    """Test label/tag management endpoints"""
    
    def test_get_tags(self, client):
        """Test GET /api/ner/tags - Get all labels"""
        response = client.get('/api/ner/tags')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
    
    def test_create_tag(self, client):
        """Test POST /api/ner/tags - Create new label"""
        tag_data = {
            'value': 'PERSON',
            'background': '#ff0000',
            'hotkey': 'p',
            'description': 'Person names',
            'example': 'John Smith'
        }
        
        response = client.post('/api/ner/tags',
                             data=json.dumps(tag_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['value'] == 'PERSON'
        assert data['hotkey'] == 'p'
    
    def test_create_tag_minimal(self, client):
        """Test creating tag with minimal data"""
        tag_data = {'value': 'ORGANIZATION'}
        
        response = client.post('/api/ner/tags',
                             data=json.dumps(tag_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['value'] == 'ORGANIZATION'
    
    def test_create_tag_no_value(self, client):
        """Test creating tag without value"""
        tag_data = {'background': '#ff0000'}
        
        response = client.post('/api/ner/tags',
                             data=json.dumps(tag_data),
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_get_tag(self, client):
        """Test GET /api/ner/tags/{tag_id} - Get specific tag"""
        # Create tag first
        tag_data = {'value': 'LOCATION', 'background': '#00ff00', 'hotkey': 'l'}
        response = client.post('/api/ner/tags',
                             data=json.dumps(tag_data),
                             content_type='application/json')
        
        tag_id = response.get_json()['id']
        
        # Get tag
        response = client.get(f'/api/ner/tags/{tag_id}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['value'] == 'LOCATION'
        assert data['hotkey'] == 'l'
    
    def test_update_tag(self, client):
        """Test PUT /api/ner/tags/{tag_id} - Update tag"""
        # Create tag first
        tag_data = {'value': 'MISCELLANEOUS'}
        response = client.post('/api/ner/tags',
                             data=json.dumps(tag_data),
                             content_type='application/json')
        
        tag_id = response.get_json()['id']
        
        # Update tag
        update_data = {
            'value': 'MISC',
            'hotkey': 'm',
            'description': 'Miscellaneous entities'
        }
        response = client.put(f'/api/ner/tags/{tag_id}',
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['value'] == 'MISC'
        assert data['hotkey'] == 'm'
    
    def test_delete_tag(self, client):
        """Test DELETE /api/ner/tags/{tag_id} - Delete tag"""
        # Create tag first
        tag_data = {'value': 'TEMPORARY'}
        response = client.post('/api/ner/tags',
                             data=json.dumps(tag_data),
                             content_type='application/json')
        
        tag_id = response.get_json()['id']
        
        # Delete tag
        response = client.delete(f'/api/ner/tags/{tag_id}')
        assert response.status_code == 200
        
        # Verify deletion
        response = client.get(f'/api/ner/tags/{tag_id}')
        assert response.status_code == 404


class TestExportAPI:
    """Test export functionality endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_annotated_task(self, client):
        """Setup task with annotations for export tests"""
        # Create task
        task_data = {'text': 'IBM was founded in New York by Thomas Watson.'}
        response = client.post('/api/ner/tasks',
                             data=json.dumps(task_data),
                             content_type='application/json')
        self.task_id = response.get_json()['task_id']
        
        # Add annotations
        annotations = [
            {'start': 0, 'end': 3, 'labels': ['ORG']},      # IBM
            {'start': 18, 'end': 26, 'labels': ['LOC']},    # New York
            {'start': 30, 'end': 42, 'labels': ['PER']},    # Thomas Watson
        ]
        
        for ann_data in annotations:
            client.post(f'/api/ner/tasks/{self.task_id}/annotations',
                       data=json.dumps(ann_data),
                       content_type='application/json')
    
    def test_export_label_studio(self, client):
        """Test GET /api/ner/tasks/{task_id}/export - Label Studio export"""
        response = client.get(f'/api/ner/tasks/{self.task_id}/export')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'id' in data
        assert 'data' in data
        assert 'annotations' in data
        assert len(data['annotations']) == 1  # One annotation entry
        assert len(data['annotations'][0]['result']) == 3  # Three annotation results
    
    def test_export_conll(self, client):
        """Test GET /api/ner/tasks/{task_id}/conll - CoNLL export"""
        response = client.get(f'/api/ner/tasks/{self.task_id}/conll')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'conll' in data
        assert isinstance(data['conll'], str)
        
        # Verify CoNLL format
        lines = data['conll'].strip().split('\n')
        assert len(lines) > 0
        
        # Check format (word \t label)
        for line in lines:
            if line.strip():
                parts = line.split('\t')
                assert len(parts) == 2
    
    def test_export_nonexistent_task(self, client):
        """Test exporting non-existent task"""
        response = client.get('/api/ner/tasks/nonexistent/export')
        assert response.status_code == 400
        
        response = client.get('/api/ner/tasks/nonexistent/conll')
        assert response.status_code == 400


class TestStatisticsAPI:
    """Test statistics endpoint"""
    
    def test_get_statistics_empty(self, client):
        """Test statistics with no data"""
        response = client.get('/api/ner/statistics')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['total_tasks'] == 0
        assert data['total_annotations'] == 0
        assert data['label_distribution'] == {}
    
    def test_get_statistics_with_data(self, client):
        """Test statistics with data"""
        # Create tasks with annotations
        tasks_data = [
            {'text': 'Apple Inc. in California.'},
            {'text': 'Google LLC in Mountain View.'}
        ]
        
        task_ids = []
        for task_data in tasks_data:
            response = client.post('/api/ner/tasks',
                                 data=json.dumps(task_data),
                                 content_type='application/json')
            task_ids.append(response.get_json()['task_id'])
        
        # Add annotations
        annotations = [
            (task_ids[0], {'start': 0, 'end': 10, 'labels': ['ORG']}),    # Apple Inc.
            (task_ids[0], {'start': 14, 'end': 24, 'labels': ['LOC']}),   # California
            (task_ids[1], {'start': 0, 'end': 10, 'labels': ['ORG']}),    # Google LLC
            (task_ids[1], {'start': 14, 'end': 27, 'labels': ['LOC']}),   # Mountain View
        ]
        
        for task_id, ann_data in annotations:
            client.post(f'/api/ner/tasks/{task_id}/annotations',
                       data=json.dumps(ann_data),
                       content_type='application/json')
        
        # Get statistics
        response = client.get('/api/ner/statistics')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['total_tasks'] == 2
        assert data['total_annotations'] == 4
        assert data['label_distribution']['ORG'] == 2
        assert data['label_distribution']['LOC'] == 2


class TestConfigurationAPI:
    """Test configuration endpoint"""
    
    def test_get_config(self, client):
        """Test GET /api/ner/config - Get configuration"""
        response = client.get('/api/ner/config')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'basic_config' in data
        assert 'enhanced_config' in data
        assert 'labels' in data
        
        # Verify XML configs are strings
        assert isinstance(data['basic_config'], str)
        assert isinstance(data['enhanced_config'], str)
        
        # Verify labels is list
        assert isinstance(data['labels'], list)


class TestFileOperationsAPI:
    """Test file save operations"""
    
    def test_save_modified_file(self, client):
        """Test POST /api/save-modified-file"""
        file_data = {
            'filename': 'test_modified.jsonl',
            'content': '{"text": "Test content", "annotations": []}'
        }
        
        response = client.post('/api/save-modified-file',
                             data=json.dumps(file_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'filename' in data
        assert 'filepath' in data
    
    def test_save_completed_file(self, client):
        """Test POST /api/save-completed-file"""
        file_data = {
            'filename': 'test_completed.jsonl',
            'content': '{"text": "Test content", "annotations": [{"start": 0, "end": 4, "labels": ["TEST"]}]}'
        }
        
        response = client.post('/api/save-completed-file',
                             data=json.dumps(file_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'completed' in data['filename']
    
    def test_save_file_no_content(self, client):
        """Test saving file without content"""
        file_data = {'filename': 'empty.jsonl'}
        
        response = client.post('/api/save-modified-file',
                             data=json.dumps(file_data),
                             content_type='application/json')
        
        assert response.status_code == 400


class TestNERInterfaceRoute:
    """Test main NER interface route"""
    
    def test_ner_interface(self, client):
        """Test GET /ner - Main interface"""
        response = client.get('/ner')
        assert response.status_code == 200
        
        # Verify HTML content
        html_content = response.get_data(as_text=True)
        assert 'NER Annotation Interface' in html_content
        assert 'labels' in html_content.lower()


class TestErrorHandling:
    """Test error handling across endpoints"""
    
    def test_invalid_json(self, client):
        """Test endpoints with invalid JSON"""
        response = client.post('/api/ner/tasks',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_missing_content_type(self, client):
        """Test POST endpoints without content type"""
        response = client.post('/api/ner/tasks',
                             data='{"text": "test"}')
        
        # Should still work or return meaningful error
        assert response.status_code in [200, 400, 415]
    
    def test_method_not_allowed(self, client):
        """Test wrong HTTP methods"""
        response = client.delete('/api/ner/tasks')  # DELETE not allowed on collection
        assert response.status_code in [404, 405]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])