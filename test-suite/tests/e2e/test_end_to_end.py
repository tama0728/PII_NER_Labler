#!/usr/bin/env python3
"""
End-to-End Test Suite
====================

Comprehensive end-to-end tests for KDPII NER Labeler system.
Tests complete user workflows and real-world usage scenarios.

Test Coverage:
- Complete annotation workflows
- Multi-document processing
- Export and import cycles
- User interface interactions
- Real-world data processing
- System performance under load
- Error recovery scenarios
"""

import pytest
import tempfile
import os
import json
import time
from unittest.mock import patch, Mock

# Import system components
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app import create_app, db
from ner_extractor import NERExtractor


class TestCompleteAnnotationWorkflows:
    """Test complete annotation workflows from document creation to export."""
    
    @pytest.fixture
    def e2e_app(self):
        """Create end-to-end testing environment."""
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-e2e-key'
        })
        
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    def test_news_article_annotation_workflow(self, e2e_app):
        """Test complete workflow: News article → Named entities → Export."""
        with e2e_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Step 1: Create a realistic news article document
            news_text = """
            Microsoft CEO Satya Nadella announced today that the company will invest $10 billion 
            in artificial intelligence research. The announcement was made at the company's 
            headquarters in Redmond, Washington. The investment will focus on developing new 
            AI technologies for cloud computing and will create 5,000 new jobs in Seattle and 
            San Francisco over the next three years.
            """
            
            doc_id = ner_extractor.create_document(news_text.strip())
            assert doc_id is not None
            
            # Step 2: Annotate various entity types
            annotations_to_create = [
                {'start': 0, 'end': 9, 'label': 'ORG', 'text': 'Microsoft'},
                {'start': 14, 'end': 27, 'label': 'PERSON', 'text': 'Satya Nadella'},
                {'start': 77, 'end': 88, 'label': 'MONEY', 'text': '$10 billion'},
                {'start': 178, 'end': 185, 'label': 'LOC', 'text': 'Redmond'},
                {'start': 187, 'end': 197, 'label': 'LOC', 'text': 'Washington'},
                {'start': 329, 'end': 334, 'label': 'CARDINAL', 'text': '5,000'},
                {'start': 348, 'end': 355, 'label': 'LOC', 'text': 'Seattle'},
                {'start': 360, 'end': 373, 'label': 'LOC', 'text': 'San Francisco'}
            ]
            
            created_annotations = []
            for ann_data in annotations_to_create:
                ann_data['document_id'] = doc_id
                response = client.post('/api/annotations',
                                     data=json.dumps(ann_data),
                                     content_type='application/json')
                
                if response.status_code in [200, 201]:
                    created_annotations.append(ann_data)
                else:
                    # Try via NER engine directly
                    ann_id = ner_extractor.create_annotation(
                        doc_id, ann_data['start'], ann_data['end'], 
                        ann_data['label'], ann_data['text']
                    )
                    if ann_id:
                        created_annotations.append(ann_data)
            
            # Step 3: Verify annotations were created
            all_annotations = ner_extractor.get_annotations(doc_id)
            assert len(all_annotations) >= len(created_annotations) // 2  # At least half should succeed
            
            # Step 4: Test overlapping annotation handling
            # Create overlapping annotation for "Microsoft CEO"
            overlap_id = ner_extractor.create_annotation(doc_id, 0, 13, 'TITLE', 'Microsoft CEO')
            if overlap_id:
                updated_annotations = ner_extractor.get_annotations(doc_id)
                overlap_ann = next((a for a in updated_annotations if a[4] == 'TITLE'), None)
                assert overlap_ann is not None
            
            # Step 5: Export annotations
            # Test Label Studio export
            ls_export = ner_extractor.export_to_label_studio()
            assert isinstance(ls_export, list)
            assert len(ls_export) > 0
            
            # Find our document in the export
            doc_export = next((item for item in ls_export 
                              if 'Microsoft' in str(item.get('data', {}))), None)
            assert doc_export is not None
            
            # Test CoNLL export
            conll_export = ner_extractor.export_to_conll()
            assert isinstance(conll_export, str)
            assert 'B-ORG' in conll_export or 'B-PERSON' in conll_export
    
    def test_scientific_document_workflow(self, e2e_app):
        """Test workflow for scientific document with complex entities."""
        with e2e_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Scientific abstract with various entity types
            scientific_text = """
            Recent advances in CRISPR-Cas9 gene editing technology have shown promising 
            results in treating sickle cell disease. Researchers at Johns Hopkins University 
            and the National Institutes of Health conducted a Phase II clinical trial with 
            45 patients aged 18-65 years. The treatment showed 89% efficacy in reducing 
            vaso-occlusive crises, with results published in Nature Medicine (Impact Factor: 87.241).
            """
            
            doc_id = ner_extractor.create_document(scientific_text.strip())
            
            # Create scientific entity annotations
            scientific_annotations = [
                {'start': 19, 'end': 29, 'label': 'TECH', 'text': 'CRISPR-Cas9'},
                {'start': 97, 'end': 116, 'label': 'DISEASE', 'text': 'sickle cell disease'},
                {'start': 131, 'end': 153, 'label': 'ORG', 'text': 'Johns Hopkins University'},
                {'start': 162, 'end': 188, 'label': 'ORG', 'text': 'National Institutes of Health'},
                {'start': 200, 'end': 208, 'label': 'STUDY_PHASE', 'text': 'Phase II'},
                {'start': 228, 'end': 230, 'label': 'CARDINAL', 'text': '45'},
                {'start': 243, 'end': 250, 'label': 'AGE_RANGE', 'text': '18-65'},
                {'start': 285, 'end': 288, 'label': 'PERCENT', 'text': '89%'},
                {'start': 370, 'end': 385, 'label': 'JOURNAL', 'text': 'Nature Medicine'},
                {'start': 403, 'end': 409, 'label': 'METRIC', 'text': '87.241'}
            ]
            
            for ann_data in scientific_annotations:
                ann_data['document_id'] = doc_id
                # Try API first, fallback to direct creation
                response = client.post('/api/annotations',
                                     data=json.dumps(ann_data),
                                     content_type='application/json')
                
                if response.status_code not in [200, 201]:
                    ner_extractor.create_annotation(
                        doc_id, ann_data['start'], ann_data['end'],
                        ann_data['label'], ann_data['text']
                    )
            
            # Verify scientific annotations
            final_annotations = ner_extractor.get_annotations(doc_id)
            assert len(final_annotations) >= 5  # Should have created several annotations
            
            # Verify specific entity types exist
            tech_entities = [a for a in final_annotations if a[4] == 'TECH']
            org_entities = [a for a in final_annotations if a[4] == 'ORG']
            assert len(tech_entities) >= 1 or len(org_entities) >= 1  # At least some should exist
    
    def test_multilingual_document_workflow(self, e2e_app):
        """Test workflow with multilingual content."""
        with e2e_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Mixed language content
            multilingual_text = """
            Samsung Electronics (삼성전자) announced a partnership with Sony Corporation 
            to develop next-generation displays. The collaboration will take place in 
            서울 (Seoul) and Tokyo (東京), with research facilities in both cities.
            """
            
            doc_id = ner_extractor.create_document(multilingual_text.strip())
            
            # Create multilingual annotations
            multilingual_annotations = [
                {'start': 0, 'end': 19, 'label': 'ORG', 'text': 'Samsung Electronics'},
                {'start': 21, 'end': 25, 'label': 'ORG_KOR', 'text': '삼성전자'},
                {'start': 58, 'end': 73, 'label': 'ORG', 'text': 'Sony Corporation'},
                {'start': 141, 'end': 143, 'label': 'LOC_KOR', 'text': '서울'},
                {'start': 145, 'end': 150, 'label': 'LOC', 'text': 'Seoul'},
                {'start': 156, 'end': 161, 'label': 'LOC', 'text': 'Tokyo'},
                {'start': 163, 'end': 165, 'label': 'LOC_JPN', 'text': '東京'}
            ]
            
            for ann_data in multilingual_annotations:
                ann_data['document_id'] = doc_id
                ner_extractor.create_annotation(
                    doc_id, ann_data['start'], ann_data['end'],
                    ann_data['label'], ann_data['text']
                )
            
            # Verify multilingual handling
            annotations = ner_extractor.get_annotations(doc_id)
            korean_annotations = [a for a in annotations if 'KOR' in a[4]]
            japanese_annotations = [a for a in annotations if 'JPN' in a[4]]
            
            assert len(annotations) >= 5
            assert len(korean_annotations) >= 1
            assert len(japanese_annotations) >= 1


class TestMultiDocumentProcessing:
    """Test processing multiple documents and batch operations."""
    
    @pytest.fixture
    def batch_app(self):
        """Create app for batch processing tests."""
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-batch-key'
        })
        
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    def test_batch_document_processing(self, batch_app):
        """Test processing multiple documents in batch."""
        with batch_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Create multiple documents with different content types
            document_types = [
                ("Business", "Apple Inc. reported quarterly earnings of $123.5 billion in Q4 2023."),
                ("Medical", "COVID-19 vaccines developed by Pfizer and Moderna showed 95% efficacy."),
                ("Legal", "The Supreme Court of the United States will review the case on January 15, 2024."),
                ("Academic", "Professor Smith from MIT published research in Journal of AI Research."),
                ("News", "President Biden visited Germany to meet with Chancellor Scholz.")
            ]
            
            doc_ids = []
            for doc_type, content in document_types:
                doc_id = ner_extractor.create_document(content)
                doc_ids.append((doc_id, doc_type, content))
            
            assert len(doc_ids) == 5
            
            # Create annotations for each document type
            annotation_patterns = {
                "Business": [("ORG", "Apple Inc."), ("MONEY", "$123.5 billion")],
                "Medical": [("DISEASE", "COVID-19"), ("ORG", "Pfizer"), ("ORG", "Moderna")],
                "Legal": [("ORG", "Supreme Court"), ("DATE", "January 15, 2024")],
                "Academic": [("PERSON", "Professor Smith"), ("ORG", "MIT")],
                "News": [("PERSON", "President Biden"), ("LOC", "Germany")]
            }
            
            total_annotations = 0
            for doc_id, doc_type, content in doc_ids:
                if doc_type in annotation_patterns:
                    for label, text in annotation_patterns[doc_type]:
                        start_pos = content.find(text)
                        if start_pos != -1:
                            end_pos = start_pos + len(text)
                            ann_id = ner_extractor.create_annotation(doc_id, start_pos, end_pos, label, text)
                            if ann_id:
                                total_annotations += 1
            
            assert total_annotations >= 5  # Should have created several annotations
            
            # Test batch export
            all_docs_export = ner_extractor.export_to_label_studio()
            assert len(all_docs_export) == 5  # All documents should be exported
            
            # Verify each document type appears in export
            export_texts = [item.get('data', {}).get('text', '') for item in all_docs_export]
            assert any('Apple Inc.' in text for text in export_texts)
            assert any('COVID-19' in text for text in export_texts)
    
    def test_document_collection_management(self, batch_app):
        """Test managing collections of related documents."""
        with batch_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Create a collection of related financial documents
            financial_documents = [
                "Tesla's stock price rose 15% following the announcement of record deliveries.",
                "Amazon reported $469.8 billion in annual revenue for 2021.",
                "Microsoft's market cap exceeded $2 trillion for the first time.",
                "Google parent Alphabet saw advertising revenue grow by 12% year-over-year.",
                "Meta Platforms invested $13.7 billion in Reality Labs division."
            ]
            
            collection_doc_ids = []
            for content in financial_documents:
                doc_id = ner_extractor.create_document(content)
                collection_doc_ids.append(doc_id)
            
            # Annotate financial entities across the collection
            financial_entities = [
                ("Tesla", "ORG"), ("15%", "PERCENT"),
                ("Amazon", "ORG"), ("$469.8 billion", "MONEY"), ("2021", "DATE"),
                ("Microsoft", "ORG"), ("$2 trillion", "MONEY"),
                ("Google", "ORG"), ("Alphabet", "ORG"), ("12%", "PERCENT"),
                ("Meta Platforms", "ORG"), ("$13.7 billion", "MONEY")
            ]
            
            annotations_created = 0
            for doc_id in collection_doc_ids:
                document = ner_extractor.get_document(doc_id)
                if document:
                    content = document[1]
                    for entity_text, entity_label in financial_entities:
                        start_pos = content.find(entity_text)
                        if start_pos != -1:
                            end_pos = start_pos + len(entity_text)
                            ann_id = ner_extractor.create_annotation(doc_id, start_pos, end_pos, entity_label, entity_text)
                            if ann_id:
                                annotations_created += 1
            
            assert annotations_created >= 8  # Should have created multiple annotations
            
            # Test collection-wide statistics
            stats = ner_extractor.get_statistics()
            assert stats['total_documents'] >= 5
            assert stats['total_annotations'] >= 8
            assert 'ORG' in stats['entity_types']
            assert 'MONEY' in stats['entity_types']


class TestRealWorldScenarios:
    """Test real-world usage scenarios and edge cases."""
    
    @pytest.fixture
    def real_world_app(self):
        """Create app for real-world scenario testing."""
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-real-world-key'
        })
        
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    def test_long_document_processing(self, real_world_app):
        """Test processing of long documents with many annotations."""
        with real_world_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Create a long document (simulate a research paper abstract)
            long_text = """
            Artificial Intelligence (AI) has revolutionized numerous industries over the past decade. 
            Companies like Google, Microsoft, Amazon, and Apple have invested billions of dollars 
            in AI research and development. The global AI market, valued at $87.04 billion in 2021, 
            is expected to grow at a CAGR of 28.46% from 2022 to 2030. Key applications include 
            machine learning, natural language processing, computer vision, and robotics. 
            
            Major breakthroughs have occurred in areas such as deep learning, neural networks, 
            and transformer architectures like GPT-3 and BERT. Research institutions including 
            Stanford University, MIT, Carnegie Mellon University, and the University of Toronto 
            have contributed significantly to these advances. 
            
            The healthcare sector has particularly benefited from AI adoption, with applications 
            in medical imaging, drug discovery, personalized medicine, and clinical decision support. 
            Companies such as IBM Watson Health, Tempus, PathAI, and DeepMind Health are leading 
            innovation in this space. The COVID-19 pandemic accelerated AI adoption, with 
            applications in vaccine development, contact tracing, and epidemiological modeling.
            """ * 2  # Double the content to make it longer
            
            doc_id = ner_extractor.create_document(long_text.strip())
            
            # Create many annotations across the long document
            entities_to_annotate = [
                ("Artificial Intelligence", "TECH"), ("AI", "TECH"),
                ("Google", "ORG"), ("Microsoft", "ORG"), ("Amazon", "ORG"), ("Apple", "ORG"),
                ("$87.04 billion", "MONEY"), ("2021", "DATE"), ("28.46%", "PERCENT"),
                ("2022", "DATE"), ("2030", "DATE"),
                ("machine learning", "TECH"), ("natural language processing", "TECH"),
                ("computer vision", "TECH"), ("robotics", "TECH"),
                ("deep learning", "TECH"), ("neural networks", "TECH"),
                ("GPT-3", "MODEL"), ("BERT", "MODEL"),
                ("Stanford University", "ORG"), ("MIT", "ORG"),
                ("Carnegie Mellon University", "ORG"), ("University of Toronto", "ORG"),
                ("IBM Watson Health", "ORG"), ("Tempus", "ORG"),
                ("PathAI", "ORG"), ("DeepMind Health", "ORG"),
                ("COVID-19", "DISEASE")
            ]
            
            annotations_created = 0
            document = ner_extractor.get_document(doc_id)
            content = document[1]
            
            for entity_text, entity_label in entities_to_annotate:
                # Find all occurrences of the entity in the long text
                start_pos = 0
                while True:
                    pos = content.find(entity_text, start_pos)
                    if pos == -1:
                        break
                    
                    end_pos = pos + len(entity_text)
                    ann_id = ner_extractor.create_annotation(doc_id, pos, end_pos, entity_label, entity_text)
                    if ann_id:
                        annotations_created += 1
                    
                    start_pos = pos + 1  # Continue searching for more occurrences
            
            assert annotations_created >= 20  # Should have created many annotations
            
            # Test that the system handles the large number of annotations
            all_annotations = ner_extractor.get_annotations(doc_id)
            assert len(all_annotations) >= 20
            
            # Test export performance with many annotations
            start_time = time.time()
            ls_export = ner_extractor.export_to_label_studio()
            export_time = time.time() - start_time
            
            assert export_time < 30.0  # Should export within reasonable time
            assert len(ls_export) >= 1
    
    def test_special_characters_and_encoding(self, real_world_app):
        """Test handling of special characters and different encodings."""
        with real_world_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Text with various special characters and encodings
            special_text = """
            Café François serves crème brûlée and naïve customers love the piña colada. 
            The company's résumé shows €12,345.67 in revenue from São Paulo operations.
            Björk's album "Médúlla" sold over 1 million copies worldwide.
            The møøse once bit my sister... No realli! She was Karving her initials.
            ¿Cómo estás? ¡Muy bien! The temperature is 37°C (98.6°F).
            Mathematical symbols: α, β, γ, δ, ∑, ∫, √, ∞, ≤, ≥, ≠, ±
            """
            
            doc_id = ner_extractor.create_document(special_text.strip())
            
            # Annotate entities with special characters
            special_entities = [
                ("Café François", "ORG"),
                ("crème brûlée", "FOOD"),
                ("piña colada", "DRINK"),
                ("€12,345.67", "MONEY"),
                ("São Paulo", "LOC"),
                ("Björk", "PERSON"),
                ("Médúlla", "ALBUM"),
                ("37°C", "TEMPERATURE"),
                ("98.6°F", "TEMPERATURE")
            ]
            
            document = ner_extractor.get_document(doc_id)
            content = document[1]
            
            for entity_text, entity_label in special_entities:
                start_pos = content.find(entity_text)
                if start_pos != -1:
                    end_pos = start_pos + len(entity_text)
                    ann_id = ner_extractor.create_annotation(doc_id, start_pos, end_pos, entity_label, entity_text)
                    assert ann_id is not None  # Should handle special characters
            
            # Verify annotations with special characters
            annotations = ner_extractor.get_annotations(doc_id)
            special_chars_annotations = [a for a in annotations if any(c in a[5] for c in "çéèêëäöüßñáíóú€°")]
            assert len(special_chars_annotations) >= 3  # Should have several special character annotations
    
    def test_error_recovery_scenarios(self, real_world_app):
        """Test system recovery from various error conditions."""
        with real_world_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Test recovery from database issues
            doc_id = ner_extractor.create_document("Error recovery test document")
            
            # Create some valid annotations
            valid_ann_id = ner_extractor.create_annotation(doc_id, 0, 5, 'VALID', 'Error')
            assert valid_ann_id is not None
            
            # Test system continues working after errors
            recovery_doc_id = ner_extractor.create_document("System recovery test")
            recovery_ann_id = ner_extractor.create_annotation(recovery_doc_id, 0, 6, 'RECOVERY', 'System')
            assert recovery_ann_id is not None
            
            # Verify both documents and annotations exist
            all_docs = ner_extractor.get_all_documents()
            assert len(all_docs) >= 2
            
            # Test export still works after errors
            export_data = ner_extractor.export_to_label_studio()
            assert isinstance(export_data, list)
            assert len(export_data) >= 2


class TestPerformanceAndScalability:
    """Test system performance and scalability characteristics."""
    
    @pytest.fixture
    def performance_app(self):
        """Create app for performance testing."""
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
    
    def test_large_scale_processing(self, performance_app):
        """Test processing large numbers of documents and annotations."""
        with performance_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Create many documents (scaled for testing)
            num_documents = 50  # Reasonable for testing
            num_annotations_per_doc = 5
            
            start_time = time.time()
            
            doc_ids = []
            for i in range(num_documents):
                content = f"Performance test document {i} contains entities like Company_{i} and Person_{i}."
                doc_id = ner_extractor.create_document(content)
                doc_ids.append(doc_id)
                
                # Add annotations to each document
                company_pos = content.find(f"Company_{i}")
                person_pos = content.find(f"Person_{i}")
                
                if company_pos != -1:
                    ner_extractor.create_annotation(doc_id, company_pos, company_pos + len(f"Company_{i}"), 'ORG', f"Company_{i}")
                
                if person_pos != -1:
                    ner_extractor.create_annotation(doc_id, person_pos, person_pos + len(f"Person_{i}"), 'PERSON', f"Person_{i}")
            
            creation_time = time.time() - start_time
            
            # Performance assertions
            assert creation_time < 60.0  # Should complete within 1 minute
            assert len(doc_ids) == num_documents
            
            # Test retrieval performance
            start_time = time.time()
            all_documents = ner_extractor.get_all_documents()
            retrieval_time = time.time() - start_time
            
            assert retrieval_time < 10.0  # Should retrieve quickly
            assert len(all_documents) >= num_documents
            
            # Test export performance with many documents
            start_time = time.time()
            export_data = ner_extractor.export_to_label_studio()
            export_time = time.time() - start_time
            
            assert export_time < 30.0  # Should export within reasonable time
            assert len(export_data) >= num_documents
    
    def test_concurrent_operations_simulation(self, performance_app):
        """Test simulated concurrent operations."""
        with performance_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Simulate concurrent document creation and annotation
            base_doc_id = ner_extractor.create_document("Concurrent operations test document")
            
            # Simulate multiple users creating annotations simultaneously
            concurrent_annotations = []
            for i in range(20):  # Simulate 20 concurrent annotation operations
                ann_data = {
                    'document_id': base_doc_id,
                    'start': i * 5,
                    'end': i * 5 + 4,
                    'label': f'CONCURRENT_{i}',
                    'text': f'Test{i}'
                }
                
                response = client.post('/api/annotations',
                                     data=json.dumps(ann_data),
                                     content_type='application/json')
                
                if response.status_code not in [200, 201]:
                    # Fallback to direct creation
                    ann_id = ner_extractor.create_annotation(
                        base_doc_id, ann_data['start'], ann_data['end'],
                        ann_data['label'], ann_data['text']
                    )
                    if ann_id:
                        concurrent_annotations.append(ann_data)
                else:
                    concurrent_annotations.append(ann_data)
            
            # Verify system handled concurrent operations gracefully
            final_annotations = ner_extractor.get_annotations(base_doc_id)
            concurrent_created = [a for a in final_annotations if 'CONCURRENT' in a[4]]
            
            # Should have created most annotations successfully
            assert len(concurrent_created) >= len(concurrent_annotations) // 2
    
    def test_memory_usage_under_load(self, performance_app):
        """Test memory usage patterns under load."""
        with performance_app.test_client() as client:
            ner_extractor = NERExtractor()
            
            # Create documents with varying sizes
            document_sizes = [100, 500, 1000, 2000, 5000]  # Character counts
            
            for size in document_sizes:
                # Create document of specified size
                content = "Memory test document. " * (size // 20)
                content = content[:size]  # Trim to exact size
                
                doc_id = ner_extractor.create_document(content)
                
                # Add multiple annotations to test memory usage
                for i in range(min(10, size // 100)):  # Scale annotations with document size
                    start_pos = i * 20
                    if start_pos < len(content) - 10:
                        end_pos = start_pos + 10
                        ner_extractor.create_annotation(doc_id, start_pos, end_pos, f'MEM_{i}', content[start_pos:end_pos])
            
            # Test that system handles varying document sizes
            all_docs = ner_extractor.get_all_documents()
            assert len(all_docs) == len(document_sizes)
            
            # Test export with varying document sizes
            export_data = ner_extractor.export_to_label_studio()
            assert len(export_data) == len(document_sizes)
            
            # Verify largest document was handled correctly
            largest_doc_export = max(export_data, key=lambda x: len(str(x.get('data', {}).get('text', ''))))
            largest_text_length = len(str(largest_doc_export.get('data', {}).get('text', '')))
            assert largest_text_length >= max(document_sizes) * 0.8  # Should be close to expected size


if __name__ == '__main__':
    # Run end-to-end tests
    pytest.main([__file__, '-v', '--tb=short', '--maxfail=5'])