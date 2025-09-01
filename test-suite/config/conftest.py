#!/usr/bin/env python3
"""
Test Configuration and Shared Fixtures
======================================

Shared pytest fixtures and configuration for the KDPII NER Labeler test suite.
Provides common test setup, teardown, and utility functions for all test modules.

Features:
- Application factory fixtures
- Database setup and cleanup
- Test data generation
- Mock configurations
- Performance profiling
- Error handling utilities
"""

import pytest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch
import json
import sqlite3
from datetime import datetime
import sys

# Add project root to path (go up two levels from config directory)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import application components
try:
    from app import create_app, db
    from ner_extractor import NERExtractor
    APP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import application components: {e}")
    APP_AVAILABLE = False


# Test Configuration
# ==================

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration settings."""
    return {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key-do-not-use-in-production',
        'WTF_CSRF_ENABLED': False,
        'DEBUG': True,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    }


@pytest.fixture(scope="session")
def temp_dir():
    """Create and cleanup temporary directory for tests."""
    temp_path = tempfile.mkdtemp(prefix='kdpii_test_')
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path, ignore_errors=True)


# Application Fixtures
# ===================

@pytest.fixture
def app(test_config):
    """Create Flask application for testing."""
    if not APP_AVAILABLE:
        pytest.skip("Application components not available")
    
    app = create_app()
    app.config.update(test_config)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Provide Flask application context."""
    with app.app_context():
        yield app


# Database Fixtures
# ================

@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        db_path = temp_db.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        try:
            os.unlink(db_path)
        except OSError:
            pass


@pytest.fixture
def ner_extractor(temp_db):
    """Create NER extractor with temporary database."""
    if not APP_AVAILABLE:
        pytest.skip("NER extractor not available")
    
    extractor = NERExtractor(db_file=temp_db)
    yield extractor


@pytest.fixture
def populated_db(ner_extractor):
    """Create database populated with test data."""
    # Create test documents
    doc1_id = ner_extractor.create_document("Test document 1 with John Doe and Microsoft.")
    doc2_id = ner_extractor.create_document("Test document 2 with Jane Smith and Apple Inc.")
    doc3_id = ner_extractor.create_document("Test document 3 with Bob Johnson and Google LLC.")
    
    # Create test annotations
    test_data = [
        (doc1_id, 19, 27, 'PERSON', 'John Doe'),
        (doc1_id, 32, 41, 'ORG', 'Microsoft'),
        (doc2_id, 19, 29, 'PERSON', 'Jane Smith'),
        (doc2_id, 34, 44, 'ORG', 'Apple Inc.'),
        (doc3_id, 19, 30, 'PERSON', 'Bob Johnson'),
        (doc3_id, 35, 45, 'ORG', 'Google LLC')
    ]
    
    annotation_ids = []
    for doc_id, start, end, label, text in test_data:
        ann_id = ner_extractor.create_annotation(doc_id, start, end, label, text)
        if ann_id:
            annotation_ids.append(ann_id)
    
    return {
        'extractor': ner_extractor,
        'doc_ids': [doc1_id, doc2_id, doc3_id],
        'annotation_ids': annotation_ids
    }


# Test Data Fixtures
# ==================

@pytest.fixture
def sample_documents():
    """Provide sample document data for testing."""
    return [
        {
            'content': 'Apple Inc. is a technology company founded by Steve Jobs.',
            'entities': [
                {'start': 0, 'end': 10, 'label': 'ORG', 'text': 'Apple Inc.'},
                {'start': 45, 'end': 55, 'label': 'PERSON', 'text': 'Steve Jobs'}
            ]
        },
        {
            'content': 'Microsoft was founded in 1975 by Bill Gates and Paul Allen.',
            'entities': [
                {'start': 0, 'end': 9, 'label': 'ORG', 'text': 'Microsoft'},
                {'start': 25, 'end': 29, 'label': 'DATE', 'text': '1975'},
                {'start': 33, 'end': 43, 'label': 'PERSON', 'text': 'Bill Gates'},
                {'start': 48, 'end': 58, 'label': 'PERSON', 'text': 'Paul Allen'}
            ]
        },
        {
            'content': 'Google LLC acquired YouTube for $1.65 billion in 2006.',
            'entities': [
                {'start': 0, 'end': 10, 'label': 'ORG', 'text': 'Google LLC'},
                {'start': 20, 'end': 27, 'label': 'ORG', 'text': 'YouTube'},
                {'start': 32, 'end': 46, 'label': 'MONEY', 'text': '$1.65 billion'},
                {'start': 50, 'end': 54, 'label': 'DATE', 'text': '2006'}
            ]
        }
    ]


@pytest.fixture
def sample_annotations():
    """Provide sample annotation data for testing."""
    return [
        {'start': 0, 'end': 5, 'label': 'PERSON', 'text': 'Alice'},
        {'start': 6, 'end': 16, 'label': 'ORG', 'text': 'Wonderland'},
        {'start': 17, 'end': 21, 'label': 'DATE', 'text': '2024'},
        {'start': 22, 'end': 32, 'label': 'MONEY', 'text': '$1,000,000'},
        {'start': 33, 'end': 41, 'label': 'LOC', 'text': 'New York'}
    ]


@pytest.fixture
def multilingual_data():
    """Provide multilingual test data."""
    return [
        {
            'content': 'Samsung Electronics (삼성전자) is based in Seoul (서울).',
            'language': 'mixed',
            'entities': [
                {'start': 0, 'end': 19, 'label': 'ORG', 'text': 'Samsung Electronics'},
                {'start': 21, 'end': 25, 'label': 'ORG_KOR', 'text': '삼성전자'},
                {'start': 38, 'end': 43, 'label': 'LOC', 'text': 'Seoul'},
                {'start': 45, 'end': 47, 'label': 'LOC_KOR', 'text': '서울'}
            ]
        },
        {
            'content': 'Nintendo (任天堂) développe des jeux vidéo depuis 1889.',
            'language': 'mixed',
            'entities': [
                {'start': 0, 'end': 8, 'label': 'ORG', 'text': 'Nintendo'},
                {'start': 10, 'end': 13, 'label': 'ORG_JPN', 'text': '任天堂'},
                {'start': 47, 'end': 51, 'label': 'DATE', 'text': '1889'}
            ]
        }
    ]


# Mock Fixtures
# =============

@pytest.fixture
def mock_request():
    """Provide mock HTTP request object."""
    mock_req = Mock()
    mock_req.json = {'test': 'data'}
    mock_req.form = {'test': 'form_data'}
    mock_req.args = {'test': 'query_param'}
    mock_req.method = 'GET'
    mock_req.content_type = 'application/json'
    return mock_req


@pytest.fixture
def mock_database():
    """Provide mock database for testing without real DB."""
    mock_db = Mock()
    mock_db.create_document.return_value = 1
    mock_db.get_document.return_value = (1, "Mock document content")
    mock_db.get_all_documents.return_value = [(1, "Mock document")]
    mock_db.create_annotation.return_value = 1
    mock_db.get_annotations.return_value = [(1, 1, 0, 5, 'TEST', 'Mock')]
    mock_db.export_to_label_studio.return_value = [{'data': {'text': 'Mock'}}]
    mock_db.export_to_conll.return_value = "Mock B-TEST"
    mock_db.get_statistics.return_value = {
        'total_documents': 1,
        'total_annotations': 1,
        'entity_types': {'TEST': 1}
    }
    return mock_db


# Utility Fixtures and Functions
# ==============================

@pytest.fixture
def performance_timer():
    """Provide performance timing utility."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.duration()
        
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


@pytest.fixture
def test_logger():
    """Provide test logging utility."""
    import logging
    
    logger = logging.getLogger('kdpii_test')
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


@pytest.fixture(autouse=True)
def test_isolation():
    """Ensure test isolation by cleaning up after each test."""
    # Setup - runs before each test
    yield
    
    # Teardown - runs after each test
    # Clean up any temporary files that might have been created
    temp_patterns = ['test_*.db', 'temp_*.json', 'debug_*.log']
    current_dir = os.getcwd()
    
    for pattern in temp_patterns:
        import glob
        for file_path in glob.glob(os.path.join(current_dir, pattern)):
            try:
                os.unlink(file_path)
            except OSError:
                pass


# Test Markers and Skipping
# =========================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )


def pytest_runtest_setup(item):
    """Setup function called before each test."""
    # Skip tests if required components are not available
    if not APP_AVAILABLE and 'unit' not in [mark.name for mark in item.iter_markers()]:
        pytest.skip("Application components not available for integration tests")


# Custom Assertions
# =================

def assert_json_response(response, status_code=200):
    """Assert that response is valid JSON with expected status code."""
    assert response.status_code == status_code
    assert response.content_type == 'application/json'
    return response.get_json()


def assert_annotation_valid(annotation):
    """Assert that annotation data is valid."""
    required_fields = ['start', 'end', 'label', 'text']
    for field in required_fields:
        assert field in annotation or len(annotation) >= 4
    
    # Check positional fields if tuple/list
    if isinstance(annotation, (list, tuple)) and len(annotation) >= 4:
        start, end = annotation[1], annotation[2]
        assert isinstance(start, int)
        assert isinstance(end, int)
        assert start < end
        assert end - start > 0


def assert_export_format_valid(export_data, format_type='labelstudio'):
    """Assert that export data has valid format."""
    assert isinstance(export_data, (list, str))
    
    if format_type == 'labelstudio':
        assert isinstance(export_data, list)
        for item in export_data:
            assert isinstance(item, dict)
            assert 'data' in item
    
    elif format_type == 'conll':
        assert isinstance(export_data, str)
        assert len(export_data.strip()) > 0


# Test Data Validation
# ====================

def validate_test_environment():
    """Validate that test environment is properly set up."""
    issues = []
    
    # Check if required modules are available
    try:
        import pytest
        import tempfile
        import sqlite3
    except ImportError as e:
        issues.append(f"Missing required module: {e}")
    
    # Check if application components are available
    if not APP_AVAILABLE:
        issues.append("Application components not available - some tests will be skipped")
    
    # Check if temp directory is writable
    try:
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(b"test")
    except Exception as e:
        issues.append(f"Temporary directory not writable: {e}")
    
    if issues:
        print("Test environment validation issues:")
        for issue in issues:
            print(f"  - {issue}")
    
    return len(issues) == 0


# Run validation on import
if __name__ == '__main__':
    validate_test_environment()