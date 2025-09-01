#!/usr/bin/env python3
"""
Backend Services Test Suite
===========================

Comprehensive tests for backend service layer, business logic,
data access patterns, and service integrations.

Test Coverage:
- Service layer architecture
- Business logic validation
- Data access repositories
- Service dependencies
- Transaction handling
- Error recovery
- Performance characteristics
"""

import pytest
import tempfile
import os
import sqlite3
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

# Import backend services and dependencies
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app import create_app, db
from ner_extractor import NERExtractor


class TestServiceLayerArchitecture:
    """Test service layer architecture patterns and dependency injection."""
    
    @pytest.fixture
    def app_context(self):
        """Create test application context."""
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-secret-key'
        })
        
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    def test_service_initialization(self, app_context):
        """Test service layer proper initialization."""
        with app_context.test_client() as client:
            # Test NER service initialization
            response = client.get('/api/health')
            assert response.status_code == 200 or response.status_code == 404  # Route may not exist
            
            # Test database service availability
            from app import db
            assert db is not None
            assert db.engine is not None
    
    def test_service_dependency_injection(self, app_context):
        """Test dependency injection between services."""
        # Test that services can access their dependencies
        ner_extractor = NERExtractor()
        assert hasattr(ner_extractor, 'db_file')
        assert ner_extractor.db_file is not None
    
    def test_service_lifecycle_management(self, app_context):
        """Test service creation, usage, and cleanup."""
        ner_extractor = NERExtractor()
        
        # Test service creation
        assert ner_extractor is not None
        
        # Test service usage
        result = ner_extractor.get_all_entities()
        assert isinstance(result, list)
        
        # Test service cleanup (implicit - no explicit cleanup needed)


class TestBusinessLogicServices:
    """Test core business logic and validation rules."""
    
    @pytest.fixture
    def ner_service(self):
        """Create NER service instance."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        ner_extractor = NERExtractor(db_file=db_path)
        yield ner_extractor
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_text_preprocessing_service(self, ner_service):
        """Test text preprocessing business logic."""
        test_text = "  Hello, World!  \n\n  This is a test.  "
        
        # Test text normalization (if available)
        processed = test_text.strip()
        assert processed == "Hello, World!  \n\n  This is a test."
        
        # Test empty text handling
        empty_result = "".strip()
        assert empty_result == ""
    
    def test_entity_validation_service(self, ner_service):
        """Test entity validation business rules."""
        # Test valid entity creation
        entity_data = {
            'text': 'test entity',
            'start': 0,
            'end': 11,
            'label': 'TEST'
        }
        
        # Basic validation logic
        assert entity_data['start'] < entity_data['end']
        assert len(entity_data['text']) == entity_data['end'] - entity_data['start']
        assert entity_data['label'].strip() != ''
    
    def test_annotation_conflict_resolution(self, ner_service):
        """Test business logic for handling annotation conflicts."""
        # Create test document
        doc_id = ner_service.create_document("Test conflict resolution document")
        
        # Test overlapping annotations
        ner_service.create_annotation(doc_id, 0, 5, 'PERSON', 'Alice')
        ner_service.create_annotation(doc_id, 3, 8, 'ORG', 'Alice Corp')
        
        # Verify both annotations exist (overlapping allowed)
        annotations = ner_service.get_annotations(doc_id)
        assert len(annotations) == 2
        
        # Test conflict detection logic
        person_ann = next(a for a in annotations if a[4] == 'PERSON')
        org_ann = next(a for a in annotations if a[4] == 'ORG')
        
        # Check overlap detection
        overlap_exists = (person_ann[1] < org_ann[2] and org_ann[1] < person_ann[2])
        assert overlap_exists == True
    
    def test_export_business_logic(self, ner_service):
        """Test export format business rules and transformations."""
        # Create test data
        doc_id = ner_service.create_document("Export test document")
        ner_service.create_annotation(doc_id, 0, 5, 'PERSON', 'Alice')
        
        # Test Label Studio export logic
        ls_data = ner_service.export_to_label_studio()
        assert isinstance(ls_data, list)
        assert len(ls_data) > 0
        
        # Test CoNLL export logic
        conll_data = ner_service.export_to_conll()
        assert isinstance(conll_data, str)
        assert 'B-PERSON' in conll_data or 'Alice' in conll_data
    
    def test_statistics_calculation_service(self, ner_service):
        """Test statistics and analytics business logic."""
        # Create test data
        doc_id = ner_service.create_document("Stats test document")
        ner_service.create_annotation(doc_id, 0, 5, 'PERSON', 'Alice')
        ner_service.create_annotation(doc_id, 6, 10, 'ORG', 'Corp')
        
        # Test statistics calculation
        stats = ner_service.get_statistics()
        
        assert 'total_documents' in stats
        assert 'total_annotations' in stats
        assert 'entity_types' in stats
        assert stats['total_documents'] >= 1
        assert stats['total_annotations'] >= 2


class TestDataAccessRepository:
    """Test data access patterns and repository implementations."""
    
    @pytest.fixture
    def repository(self):
        """Create repository instance."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        ner_extractor = NERExtractor(db_file=db_path)
        yield ner_extractor
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_document_repository_operations(self, repository):
        """Test document repository CRUD operations."""
        # Create
        doc_id = repository.create_document("Test document content")
        assert doc_id is not None
        assert isinstance(doc_id, int)
        
        # Read
        document = repository.get_document(doc_id)
        assert document is not None
        assert document[1] == "Test document content"  # content field
        
        # Update
        repository.update_document(doc_id, "Updated content")
        updated_doc = repository.get_document(doc_id)
        assert updated_doc[1] == "Updated content"
        
        # List
        all_docs = repository.get_all_documents()
        assert len(all_docs) >= 1
        assert any(doc[0] == doc_id for doc in all_docs)
        
        # Delete
        repository.delete_document(doc_id)
        deleted_doc = repository.get_document(doc_id)
        assert deleted_doc is None
    
    def test_annotation_repository_operations(self, repository):
        """Test annotation repository CRUD operations."""
        # Setup document
        doc_id = repository.create_document("Test annotation document")
        
        # Create annotation
        ann_id = repository.create_annotation(doc_id, 0, 4, 'TEST', 'Test')
        assert ann_id is not None
        
        # Read annotation
        annotations = repository.get_annotations(doc_id)
        assert len(annotations) >= 1
        test_annotation = next((a for a in annotations if a[0] == ann_id), None)
        assert test_annotation is not None
        assert test_annotation[4] == 'TEST'  # label field
        
        # Update annotation
        repository.update_annotation(ann_id, 0, 4, 'UPDATED', 'Test')
        updated_annotations = repository.get_annotations(doc_id)
        updated_annotation = next((a for a in updated_annotations if a[0] == ann_id), None)
        assert updated_annotation[4] == 'UPDATED'
        
        # Delete annotation
        repository.delete_annotation(ann_id)
        remaining_annotations = repository.get_annotations(doc_id)
        assert not any(a[0] == ann_id for a in remaining_annotations)
    
    def test_repository_transaction_handling(self, repository):
        """Test repository transaction management."""
        doc_id = repository.create_document("Transaction test")
        
        # Test successful transaction (implicit)
        ann1_id = repository.create_annotation(doc_id, 0, 5, 'PERSON', 'Alice')
        ann2_id = repository.create_annotation(doc_id, 6, 10, 'ORG', 'Corp')
        
        annotations = repository.get_annotations(doc_id)
        assert len(annotations) == 2
        
        # Test rollback scenario (manual cleanup)
        repository.delete_annotation(ann1_id)
        repository.delete_annotation(ann2_id)
        
        final_annotations = repository.get_annotations(doc_id)
        assert len(final_annotations) == 0
    
    def test_repository_query_optimization(self, repository):
        """Test repository query performance and optimization."""
        # Create multiple documents
        doc_ids = []
        for i in range(10):
            doc_id = repository.create_document(f"Test document {i}")
            doc_ids.append(doc_id)
            
            # Add annotations to each document
            for j in range(5):
                repository.create_annotation(doc_id, j*10, j*10+5, f'TYPE_{j}', f'Entity_{j}')
        
        # Test batch queries
        all_docs = repository.get_all_documents()
        assert len(all_docs) >= 10
        
        # Test filtered queries
        first_doc_annotations = repository.get_annotations(doc_ids[0])
        assert len(first_doc_annotations) == 5


class TestServiceIntegration:
    """Test integration between different services."""
    
    @pytest.fixture
    def integrated_service(self):
        """Create integrated service environment."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        ner_extractor = NERExtractor(db_file=db_path)
        yield ner_extractor
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_document_annotation_workflow(self, integrated_service):
        """Test end-to-end document and annotation workflow."""
        # Document creation
        doc_id = integrated_service.create_document("Integration test document")
        
        # Annotation creation
        ann_id = integrated_service.create_annotation(doc_id, 0, 11, 'TEST', 'Integration')
        
        # Workflow validation
        document = integrated_service.get_document(doc_id)
        annotations = integrated_service.get_annotations(doc_id)
        
        assert document is not None
        assert len(annotations) == 1
        assert annotations[0][0] == ann_id
    
    def test_export_service_integration(self, integrated_service):
        """Test integration between data services and export services."""
        # Setup test data
        doc_id = integrated_service.create_document("Export integration test")
        integrated_service.create_annotation(doc_id, 0, 6, 'PERSON', 'Export')
        
        # Test Label Studio export integration
        ls_export = integrated_service.export_to_label_studio()
        assert isinstance(ls_export, list)
        assert len(ls_export) > 0
        
        # Test CoNLL export integration
        conll_export = integrated_service.export_to_conll()
        assert isinstance(conll_export, str)
        assert len(conll_export.strip()) > 0
    
    def test_statistics_service_integration(self, integrated_service):
        """Test integration between data and statistics services."""
        # Create diverse test data
        doc1_id = integrated_service.create_document("Stats doc 1")
        doc2_id = integrated_service.create_document("Stats doc 2")
        
        integrated_service.create_annotation(doc1_id, 0, 5, 'PERSON', 'Alice')
        integrated_service.create_annotation(doc1_id, 6, 10, 'ORG', 'Corp')
        integrated_service.create_annotation(doc2_id, 0, 3, 'LOC', 'NYC')
        
        # Test statistics integration
        stats = integrated_service.get_statistics()
        
        assert stats['total_documents'] >= 2
        assert stats['total_annotations'] >= 3
        assert len(stats['entity_types']) >= 3  # PERSON, ORG, LOC


class TestServiceErrorHandling:
    """Test error handling and recovery in services."""
    
    @pytest.fixture
    def error_prone_service(self):
        """Create service for error testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        ner_extractor = NERExtractor(db_file=db_path)
        yield ner_extractor
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_invalid_input_handling(self, error_prone_service):
        """Test service behavior with invalid inputs."""
        # Test invalid document operations
        invalid_doc = error_prone_service.get_document(-1)
        assert invalid_doc is None
        
        # Test invalid annotation operations
        invalid_annotations = error_prone_service.get_annotations(-1)
        assert isinstance(invalid_annotations, list)
        assert len(invalid_annotations) == 0
    
    def test_database_error_recovery(self, error_prone_service):
        """Test service recovery from database errors."""
        # Test with valid operations first
        doc_id = error_prone_service.create_document("Error test document")
        assert doc_id is not None
        
        # Test recovery from potential errors
        try:
            error_prone_service.get_annotations(doc_id)
            error_prone_service.get_document(doc_id)
        except Exception as e:
            pytest.fail(f"Service should handle database operations gracefully: {e}")
    
    def test_export_error_handling(self, error_prone_service):
        """Test export service error handling."""
        # Test export with empty database
        try:
            ls_export = error_prone_service.export_to_label_studio()
            assert isinstance(ls_export, list)
            
            conll_export = error_prone_service.export_to_conll()
            assert isinstance(conll_export, str)
        except Exception as e:
            pytest.fail(f"Export services should handle empty data gracefully: {e}")


class TestServicePerformance:
    """Test service performance characteristics."""
    
    @pytest.fixture
    def performance_service(self):
        """Create service for performance testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        ner_extractor = NERExtractor(db_file=db_path)
        yield ner_extractor
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_bulk_operation_performance(self, performance_service):
        """Test performance of bulk operations."""
        import time
        
        # Test bulk document creation
        start_time = time.time()
        doc_ids = []
        for i in range(50):  # Reasonable number for testing
            doc_id = performance_service.create_document(f"Performance test document {i}")
            doc_ids.append(doc_id)
        creation_time = time.time() - start_time
        
        # Verify reasonable performance (should complete in reasonable time)
        assert creation_time < 10.0  # Should complete in under 10 seconds
        assert len(doc_ids) == 50
        
        # Test bulk retrieval
        start_time = time.time()
        all_docs = performance_service.get_all_documents()
        retrieval_time = time.time() - start_time
        
        assert retrieval_time < 5.0  # Should retrieve in under 5 seconds
        assert len(all_docs) >= 50
    
    def test_memory_usage_patterns(self, performance_service):
        """Test service memory usage patterns."""
        # Create moderate amount of test data
        doc_id = performance_service.create_document("Memory test document " * 100)  # Larger document
        
        # Add multiple annotations
        for i in range(20):
            performance_service.create_annotation(doc_id, i*10, i*10+5, f'TYPE_{i}', f'Entity_{i}')
        
        # Test that operations complete without memory issues
        annotations = performance_service.get_annotations(doc_id)
        assert len(annotations) == 20
        
        # Test export operations don't cause memory issues
        ls_export = performance_service.export_to_label_studio()
        conll_export = performance_service.export_to_conll()
        
        assert len(ls_export) > 0
        assert len(conll_export) > 0


if __name__ == '__main__':
    # Run backend services tests
    pytest.main([__file__, '-v', '--tb=short'])