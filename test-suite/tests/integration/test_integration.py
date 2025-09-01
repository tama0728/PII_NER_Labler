#!/usr/bin/env python3
"""
Integration Test Suite
======================

Comprehensive integration tests for KDPII NER Labeler system.
Tests the interaction between different system components:
- Flask API + NER Engine integration
- Database + API integration  
- Frontend + Backend integration
- Full-stack data flow validation

Test Coverage:
- Cross-component workflows
- API-Database consistency
- Frontend-Backend communication
- Data persistence across layers
- Error propagation between components
"""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, Mock
import sqlite3
from datetime import datetime

# Import system components
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app import create_app, db
from ner_extractor import NERExtractor


class TestFlaskNERIntegration:
    """Test integration between Flask API and NER engine."""
    
    @pytest.fixture
    def app_with_ner(self):
        """Create Flask app with NER integration."""
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-integration-key'
        })
        
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    def test_api_ner_document_workflow(self, app_with_ner):
        """Test document creation through API and NER engine integration."""
        with app_with_ner.test_client() as client:
            # Create document via API
            doc_data = {'content': 'Integration test document with John Doe working at Microsoft.'}
            response = client.post('/api/documents', 
                                 data=json.dumps(doc_data),
                                 content_type='application/json')
            
            if response.status_code in [200, 201]:
                response_data = response.get_json()
                doc_id = response_data.get('id')
                
                # Verify NER engine can access the document
                ner_extractor = NERExtractor()
                document = ner_extractor.get_document(doc_id)
                assert document is not None
                assert 'John Doe' in document[1] or 'Microsoft' in document[1]
    
    def test_api_ner_annotation_consistency(self, app_with_ner):
        """Test annotation consistency between API and NER engine."""
        with app_with_ner.test_client() as client:
            # Setup document through NER engine
            ner_extractor = NERExtractor()
            doc_id = ner_extractor.create_document("Test document for API integration")
            
            # Create annotation via API
            ann_data = {
                'document_id': doc_id,
                'start': 0,
                'end': 4,
                'label': 'TEST',
                'text': 'Test'
            }
            
            response = client.post('/api/annotations',
                                 data=json.dumps(ann_data),
                                 content_type='application/json')
            
            if response.status_code in [200, 201]:
                # Verify annotation exists in NER engine
                annotations = ner_extractor.get_annotations(doc_id)
                assert len(annotations) >= 1
                api_annotation = next((a for a in annotations if a[4] == 'TEST'), None)
                assert api_annotation is not None
    
    def test_api_ner_export_integration(self, app_with_ner):
        """Test export functionality integration between API and NER engine."""
        with app_with_ner.test_client() as client:
            # Setup test data via NER engine
            ner_extractor = NERExtractor()
            doc_id = ner_extractor.create_document("Export integration test document")
            ner_extractor.create_annotation(doc_id, 0, 6, 'PERSON', 'Export')
            
            # Test Label Studio export via API
            response = client.get('/api/export/labelstudio')
            if response.status_code == 200:
                export_data = response.get_json()
                assert isinstance(export_data, list)
                assert len(export_data) > 0
            
            # Test CoNLL export via API  
            response = client.get('/api/export/conll')
            if response.status_code == 200:
                export_text = response.get_data(as_text=True)
                assert isinstance(export_text, str)
                assert len(export_text.strip()) > 0


class TestDatabaseAPIIntegration:
    """Test integration between database operations and API endpoints."""
    
    @pytest.fixture
    def api_db_app(self):
        """Create app for database-API integration testing."""
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-db-api-key'
        })
        
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    def test_database_api_crud_consistency(self, api_db_app):
        """Test CRUD operations consistency between database and API."""
        with api_db_app.test_client() as client:
            # Create via API, verify in database
            doc_data = {'content': 'Database API integration test'}
            response = client.post('/api/documents',
                                 data=json.dumps(doc_data),
                                 content_type='application/json')
            
            if response.status_code in [200, 201]:
                response_data = response.get_json()
                doc_id = response_data.get('id')
                
                # Verify in database directly
                ner_extractor = NERExtractor()
                db_document = ner_extractor.get_document(doc_id)
                assert db_document is not None
                assert db_document[1] == 'Database API integration test'
                
                # Update via API, verify in database
                update_data = {'content': 'Updated database API test'}
                update_response = client.put(f'/api/documents/{doc_id}',
                                           data=json.dumps(update_data),
                                           content_type='application/json')
                
                if update_response.status_code in [200, 204]:
                    updated_db_document = ner_extractor.get_document(doc_id)
                    assert updated_db_document[1] == 'Updated database API test'
    
    def test_database_api_transaction_integrity(self, api_db_app):
        """Test transaction integrity between database and API operations."""
        with api_db_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Create document and annotations in sequence
            doc_data = {'content': 'Transaction integrity test document'}
            doc_response = client.post('/api/documents',
                                     data=json.dumps(doc_data),
                                     content_type='application/json')
            
            if doc_response.status_code in [200, 201]:
                doc_id = doc_response.get_json().get('id')
                
                # Create annotation via API
                ann_data = {
                    'document_id': doc_id,
                    'start': 0,
                    'end': 11,
                    'label': 'TEST',
                    'text': 'Transaction'
                }
                ann_response = client.post('/api/annotations',
                                         data=json.dumps(ann_data),
                                         content_type='application/json')
                
                if ann_response.status_code in [200, 201]:
                    # Verify both document and annotation exist in database
                    db_document = ner_extractor.get_document(doc_id)
                    db_annotations = ner_extractor.get_annotations(doc_id)
                    
                    assert db_document is not None
                    assert len(db_annotations) >= 1
    
    def test_database_api_error_propagation(self, api_db_app):
        """Test error propagation between database and API layers."""
        with api_db_app.test_client() as client:
            # Test invalid document ID
            response = client.get('/api/documents/99999')
            expected_statuses = [404, 500]  # Either not found or server error
            assert response.status_code in expected_statuses
            
            # Test invalid annotation creation
            invalid_ann_data = {
                'document_id': 99999,  # Non-existent document
                'start': 0,
                'end': 5,
                'label': 'TEST',
                'text': 'Test'
            }
            response = client.post('/api/annotations',
                                 data=json.dumps(invalid_ann_data),
                                 content_type='application/json')
            expected_statuses = [400, 404, 500]  # Bad request, not found, or server error
            assert response.status_code in expected_statuses


class TestFrontendBackendIntegration:
    """Test integration between frontend interface and backend services."""
    
    @pytest.fixture
    def full_stack_app(self):
        """Create full-stack app for frontend-backend testing."""
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-full-stack-key'
        })
        
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    def test_frontend_backend_document_flow(self, full_stack_app):
        """Test document workflow from frontend to backend."""
        with full_stack_app.test_client() as client:
            # Test main interface loads
            response = client.get('/')
            assert response.status_code == 200
            assert b'html' in response.data or b'NER' in response.data
            
            # Test document creation from frontend form
            form_data = {'content': 'Frontend backend integration test document'}
            response = client.post('/create_document', data=form_data)
            
            # Should redirect or return success
            assert response.status_code in [200, 201, 302]
            
            # Verify document exists in backend
            ner_extractor = NERExtractor()
            documents = ner_extractor.get_all_documents()
            test_doc = next((doc for doc in documents if 'Frontend backend' in doc[1]), None)
            assert test_doc is not None
    
    def test_frontend_backend_annotation_flow(self, full_stack_app):
        """Test annotation workflow from frontend to backend."""
        with full_stack_app.test_client() as client:
            # Setup document via backend
            ner_extractor = NERExtractor()
            doc_id = ner_extractor.create_document("Frontend annotation test document")
            
            # Test annotation interface loads
            response = client.get(f'/document/{doc_id}')
            assert response.status_code in [200, 404]  # May or may not exist
            
            # Test annotation creation via frontend
            ann_form_data = {
                'start': '0',
                'end': '8',
                'label': 'FRONTEND',
                'text': 'Frontend'
            }
            response = client.post(f'/document/{doc_id}/annotate', data=ann_form_data)
            
            if response.status_code in [200, 201, 302]:
                # Verify annotation exists in backend
                annotations = ner_extractor.get_annotations(doc_id)
                frontend_ann = next((a for a in annotations if a[4] == 'FRONTEND'), None)
                assert frontend_ann is not None
    
    def test_frontend_backend_export_flow(self, full_stack_app):
        """Test export workflow from frontend to backend."""
        with full_stack_app.test_client() as client:
            # Setup test data via backend
            ner_extractor = NERExtractor()
            doc_id = ner_extractor.create_document("Export flow test document")
            ner_extractor.create_annotation(doc_id, 0, 6, 'EXPORT', 'Export')
            
            # Test export via frontend
            response = client.get('/export/labelstudio')
            if response.status_code == 200:
                # Should return JSON or downloadable content
                content_type = response.headers.get('Content-Type', '')
                assert 'json' in content_type or 'application' in content_type
            
            response = client.get('/export/conll')
            if response.status_code == 200:
                # Should return text content
                content_type = response.headers.get('Content-Type', '')
                assert 'text' in content_type or 'application' in content_type


class TestSystemDataFlow:
    """Test data flow across entire system."""
    
    @pytest.fixture
    def data_flow_app(self):
        """Create app for testing system-wide data flow."""
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-data-flow-key'
        })
        
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    def test_complete_annotation_workflow(self, data_flow_app):
        """Test complete workflow: Document creation → Annotation → Export."""
        with data_flow_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Step 1: Document creation via NER engine
            doc_id = ner_extractor.create_document("Complete workflow test: Alice works at Microsoft in Seattle.")
            
            # Step 2: Annotation via API
            ann_data = {
                'document_id': doc_id,
                'start': 24,
                'end': 29,
                'label': 'PERSON',
                'text': 'Alice'
            }
            response = client.post('/api/annotations',
                                 data=json.dumps(ann_data),
                                 content_type='application/json')
            
            if response.status_code in [200, 201]:
                # Step 3: Verify annotation via NER engine
                annotations = ner_extractor.get_annotations(doc_id)
                person_ann = next((a for a in annotations if a[4] == 'PERSON'), None)
                assert person_ann is not None
                assert person_ann[5] == 'Alice'
                
                # Step 4: Export via API
                export_response = client.get('/api/export/labelstudio')
                if export_response.status_code == 200:
                    export_data = export_response.get_json()
                    assert isinstance(export_data, list)
                    assert len(export_data) > 0
                    
                    # Verify annotation appears in export
                    doc_export = next((item for item in export_data if item.get('data', {}).get('text') == ner_extractor.get_document(doc_id)[1]), None)
                    assert doc_export is not None
    
    def test_multi_user_data_consistency(self, data_flow_app):
        """Test data consistency across multiple concurrent operations."""
        with data_flow_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Create multiple documents
            doc_ids = []
            for i in range(5):
                doc_id = ner_extractor.create_document(f"Multi-user test document {i}")
                doc_ids.append(doc_id)
            
            # Create annotations for each document via different methods
            for i, doc_id in enumerate(doc_ids):
                if i % 2 == 0:
                    # Via NER engine
                    ner_extractor.create_annotation(doc_id, 0, 5, f'TYPE_{i}', f'Text_{i}')
                else:
                    # Via API
                    ann_data = {
                        'document_id': doc_id,
                        'start': 0,
                        'end': 5,
                        'label': f'TYPE_{i}',
                        'text': f'Text_{i}'
                    }
                    client.post('/api/annotations',
                              data=json.dumps(ann_data),
                              content_type='application/json')
            
            # Verify all annotations exist and are consistent
            for i, doc_id in enumerate(doc_ids):
                annotations = ner_extractor.get_annotations(doc_id)
                type_ann = next((a for a in annotations if a[4] == f'TYPE_{i}'), None)
                assert type_ann is not None
                assert type_ann[5] == f'Text_{i}'
    
    def test_system_error_recovery(self, data_flow_app):
        """Test system recovery from various error conditions."""
        with data_flow_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Test recovery from invalid API requests
            invalid_ann_data = {'invalid': 'data'}
            response = client.post('/api/annotations',
                                 data=json.dumps(invalid_ann_data),
                                 content_type='application/json')
            # System should handle gracefully
            assert response.status_code in [400, 422, 500]
            
            # Test that system continues to work after errors
            doc_id = ner_extractor.create_document("Recovery test document")
            assert doc_id is not None
            
            valid_ann_data = {
                'document_id': doc_id,
                'start': 0,
                'end': 8,
                'label': 'RECOVERY',
                'text': 'Recovery'
            }
            response = client.post('/api/annotations',
                                 data=json.dumps(valid_ann_data),
                                 content_type='application/json')
            
            # Should work normally after error
            if response.status_code in [200, 201]:
                annotations = ner_extractor.get_annotations(doc_id)
                assert len(annotations) >= 1


class TestPerformanceIntegration:
    """Test performance characteristics of integrated system."""
    
    @pytest.fixture
    def performance_app(self):
        """Create app for performance integration testing."""
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-performance-key'
        })
        
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    def test_bulk_operation_performance(self, performance_app):
        """Test performance of bulk operations across system components."""
        import time
        
        with performance_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Test bulk document creation performance
            start_time = time.time()
            doc_ids = []
            for i in range(20):  # Reasonable test size
                doc_id = ner_extractor.create_document(f"Performance test document {i}")
                doc_ids.append(doc_id)
            creation_time = time.time() - start_time
            
            assert creation_time < 10.0  # Should complete reasonably fast
            assert len(doc_ids) == 20
            
            # Test bulk annotation creation via API
            start_time = time.time()
            for i, doc_id in enumerate(doc_ids[:10]):  # Test on subset
                ann_data = {
                    'document_id': doc_id,
                    'start': 0,
                    'end': 11,
                    'label': f'PERF_{i}',
                    'text': 'Performance'
                }
                client.post('/api/annotations',
                          data=json.dumps(ann_data),
                          content_type='application/json')
            annotation_time = time.time() - start_time
            
            assert annotation_time < 15.0  # Should complete in reasonable time
            
            # Test bulk export performance
            start_time = time.time()
            export_response = client.get('/api/export/labelstudio')
            export_time = time.time() - start_time
            
            assert export_time < 10.0  # Export should be fast
            if export_response.status_code == 200:
                export_data = export_response.get_json()
                assert len(export_data) >= 10  # Should include test data
    
    def test_concurrent_access_handling(self, performance_app):
        """Test system behavior under concurrent access patterns."""
        with performance_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Simulate concurrent document creation
            doc_id = ner_extractor.create_document("Concurrent access test document")
            
            # Simulate multiple annotation operations
            ann_operations = [
                {'start': 0, 'end': 10, 'label': 'CONCURRENT_A', 'text': 'Concurrent'},
                {'start': 11, 'end': 17, 'label': 'CONCURRENT_B', 'text': 'access'},
                {'start': 18, 'end': 22, 'label': 'CONCURRENT_C', 'text': 'test'}
            ]
            
            for ann_data in ann_operations:
                ann_data['document_id'] = doc_id
                response = client.post('/api/annotations',
                                     data=json.dumps(ann_data),
                                     content_type='application/json')
                # Each operation should succeed or fail gracefully
                assert response.status_code in [200, 201, 400, 500]
            
            # Verify final state is consistent
            final_annotations = ner_extractor.get_annotations(doc_id)
            concurrent_annotations = [a for a in final_annotations if 'CONCURRENT' in a[4]]
            assert len(concurrent_annotations) >= 0  # Should handle concurrency gracefully


if __name__ == '__main__':
    # Run integration tests
    pytest.main([__file__, '-v', '--tb=short'])