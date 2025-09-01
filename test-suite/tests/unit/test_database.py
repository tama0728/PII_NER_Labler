#!/usr/bin/env python3
"""
Unit Tests for Database Operations
Tests all database models, repositories, and service layers:
- Model validation and relationships
- Repository CRUD operations
- Service layer functionality
- Database constraints and edge cases
- Migration compatibility
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app import create_app
from backend.database import db
from backend.config import Config
from backend.models.user import User
from backend.models.project import Project
from backend.models.task import Task
from backend.models.annotation import Annotation
from backend.models.label import Label
from backend.services.user_service import UserService
from backend.services.task_service import TaskService
from backend.services.annotation_service import AnnotationService
from backend.services.project_service import ProjectService
from backend.services.label_service import LabelService


class TestConfig(Config):
    """Test configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


@pytest.fixture
def app():
    """Create test app with in-memory database"""
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def db_session(app):
    """Database session for tests"""
    with app.app_context():
        yield db.session


class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self, db_session):
        """Test basic user creation"""
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('password123')
        assert not user.check_password('wrongpassword')
    
    def test_user_validation(self, db_session):
        """Test user field validation"""
        # Missing required fields should raise error
        user = User()
        db_session.add(user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_unique_constraints(self, db_session):
        """Test unique constraints on username and email"""
        user1 = User(username='testuser', email='test@example.com')
        user1.set_password('password')
        db_session.add(user1)
        db_session.commit()
        
        # Duplicate username
        user2 = User(username='testuser', email='different@example.com')
        user2.set_password('password')
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
        
        # Duplicate email
        user3 = User(username='differentuser', email='test@example.com')
        user3.set_password('password')
        db_session.add(user3)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_relationships(self, db_session):
        """Test user relationships with projects"""
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db_session.add(user)
        db_session.commit()
        
        project = Project(
            name='Test Project',
            description='Test description',
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()
        
        assert len(user.projects) == 1
        assert user.projects[0].name == 'Test Project'


class TestProjectModel:
    """Test Project model functionality"""
    
    @pytest.fixture
    def test_user(self, db_session):
        """Create test user for project tests"""
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db_session.add(user)
        db_session.commit()
        return user
    
    def test_project_creation(self, db_session, test_user):
        """Test basic project creation"""
        project = Project(
            name='NER Project',
            description='Named Entity Recognition project',
            owner_id=test_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        assert project.id is not None
        assert project.name == 'NER Project'
        assert project.is_active is True
        assert project.allow_overlapping_annotations is True
        assert project.owner_id == test_user.id
    
    def test_project_relationships(self, db_session, test_user):
        """Test project relationships"""
        project = Project(
            name='Test Project',
            owner_id=test_user.id
        )
        db_session.add(project)
        db_session.commit()
        
        # Test owner relationship
        assert project.owner.username == 'testuser'
        
        # Test tasks relationship
        task = Task(
            text='Sample text',
            project_id=project.id
        )
        db_session.add(task)
        db_session.commit()
        
        assert len(project.tasks) == 1
        assert project.tasks[0].text == 'Sample text'


class TestTaskModel:
    """Test Task model functionality"""
    
    @pytest.fixture
    def test_project(self, db_session):
        """Create test project for task tests"""
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db_session.add(user)
        db_session.commit()
        
        project = Project(name='Test Project', owner_id=user.id)
        db_session.add(project)
        db_session.commit()
        return project
    
    def test_task_creation(self, db_session, test_project):
        """Test basic task creation"""
        task = Task(
            text='Apple Inc. was founded by Steve Jobs.',
            project_id=test_project.id
        )
        db_session.add(task)
        db_session.commit()
        
        assert task.id is not None
        assert task.uuid is not None
        assert task.text == 'Apple Inc. was founded by Steve Jobs.'
        assert task.is_completed is False
        assert task.identifier_type == 'default'
    
    def test_task_validation(self, db_session, test_project):
        """Test task field validation"""
        # Empty text should be allowed
        task = Task(text='', project_id=test_project.id)
        db_session.add(task)
        db_session.commit()
        
        assert task.text == ''
    
    def test_task_completion(self, db_session, test_project):
        """Test task completion functionality"""
        task = Task(text='Test task', project_id=test_project.id)
        db_session.add(task)
        db_session.commit()
        
        # Mark as completed
        task.mark_completed()
        
        assert task.is_completed is True
        assert task.completion_time is not None
    
    def test_task_relationships(self, db_session, test_project):
        """Test task relationships with annotations"""
        task = Task(text='Google LLC', project_id=test_project.id)
        db_session.add(task)
        db_session.commit()
        
        annotation = Annotation(
            start=0,
            end=10,
            text='Google LLC',
            labels=['ORG'],
            task_id=task.id
        )
        db_session.add(annotation)
        db_session.commit()
        
        assert len(task.annotations) == 1
        assert task.annotations[0].text == 'Google LLC'


class TestAnnotationModel:
    """Test Annotation model functionality"""
    
    @pytest.fixture
    def test_task(self, db_session):
        """Create test task for annotation tests"""
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db_session.add(user)
        db_session.commit()
        
        project = Project(name='Test Project', owner_id=user.id)
        db_session.add(project)
        db_session.commit()
        
        task = Task(text='Microsoft Corporation', project_id=project.id)
        db_session.add(task)
        db_session.commit()
        return task
    
    def test_annotation_creation(self, db_session, test_task):
        """Test basic annotation creation"""
        annotation = Annotation(
            start=0,
            end=9,
            text='Microsoft',
            labels=['ORG'],
            task_id=test_task.id
        )
        db_session.add(annotation)
        db_session.commit()
        
        assert annotation.id is not None
        assert annotation.uuid is not None
        assert annotation.start == 0
        assert annotation.end == 9
        assert annotation.text == 'Microsoft'
        assert annotation.labels == ['ORG']
        assert annotation.confidence == 'high'
        assert annotation.identifier_type == 'default'
        assert annotation.overlapping is False
    
    def test_annotation_validation(self, db_session, test_task):
        """Test annotation validation"""
        # Invalid span (start >= end)
        with pytest.raises(ValueError, match="Invalid annotation span"):
            annotation = Annotation(
                start=10,
                end=5,
                text='Invalid',
                labels=['TEST'],
                task_id=test_task.id
            )
            annotation.__post_init__()
    
    def test_annotation_methods(self, db_session, test_task):
        """Test annotation utility methods"""
        annotation = Annotation(
            start=0,
            end=9,
            text='Microsoft',
            labels=['ORG'],
            task_id=test_task.id
        )
        db_session.add(annotation)
        db_session.commit()
        
        # Test span_length
        assert annotation.span_length == 9
        
        # Test confidence setting
        annotation.set_confidence('low')
        assert annotation.confidence == 'low'
        
        # Test label management
        annotation.add_label('COMPANY')
        assert 'COMPANY' in annotation.labels
        
        annotation.remove_label('ORG')
        assert 'ORG' not in annotation.labels
        
        # Test identifier type
        annotation.set_identifier_type('quasi')
        assert annotation.identifier_type == 'quasi'
        
        # Test overlapping flag
        annotation.set_overlapping(True)
        assert annotation.overlapping is True
    
    def test_annotation_overlap_detection(self, db_session, test_task):
        """Test annotation overlap detection methods"""
        ann1 = Annotation(
            start=0,
            end=10,
            text='Microsoft',
            labels=['ORG'],
            task_id=test_task.id
        )
        
        ann2 = Annotation(
            start=5,
            end=15,
            text='soft Corp',
            labels=['ORG'],
            task_id=test_task.id
        )
        
        ann3 = Annotation(
            start=20,
            end=25,
            text='Other',
            labels=['MISC'],
            task_id=test_task.id
        )
        
        # Test overlaps_with
        assert ann1.overlaps_with(ann2)
        assert ann2.overlaps_with(ann1)
        assert not ann1.overlaps_with(ann3)
        
        # Test containment
        ann_large = Annotation(
            start=0,
            end=20,
            text='Microsoft Corporation',
            labels=['ORG'],
            task_id=test_task.id
        )
        
        assert ann_large.contains(ann1)
        assert ann1.is_contained_by(ann_large)
        assert not ann1.contains(ann_large)
    
    def test_annotation_serialization(self, db_session, test_task):
        """Test annotation to_dict and Label Studio export"""
        annotation = Annotation(
            start=0,
            end=9,
            text='Microsoft',
            labels=['ORG'],
            confidence='high',
            notes='Test annotation',
            task_id=test_task.id
        )
        db_session.add(annotation)
        db_session.commit()
        
        # Test to_dict
        result = annotation.to_dict()
        expected_keys = [
            'id', 'uuid', 'start', 'end', 'text', 'labels', 
            'confidence', 'notes', 'span_length', 'identifier_type',
            'overlapping', 'relationships'
        ]
        
        for key in expected_keys:
            assert key in result
        
        # Test Label Studio format
        ls_result = annotation.to_label_studio_result()
        assert ls_result['type'] == 'labels'
        assert ls_result['value']['text'] == 'Microsoft'
        assert ls_result['value']['labels'] == ['ORG']


class TestLabelModel:
    """Test Label model functionality"""
    
    @pytest.fixture
    def test_project(self, db_session):
        """Create test project for label tests"""
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db_session.add(user)
        db_session.commit()
        
        project = Project(name='Test Project', owner_id=user.id)
        db_session.add(project)
        db_session.commit()
        return project
    
    def test_label_creation(self, db_session, test_project):
        """Test basic label creation"""
        label = Label(
            value='PERSON',
            background='#ff0000',
            hotkey='p',
            category='Entity',
            description='Person names',
            example='John Smith',
            project_id=test_project.id
        )
        db_session.add(label)
        db_session.commit()
        
        assert label.id is not None
        assert label.value == 'PERSON'
        assert label.background == '#ff0000'
        assert label.hotkey == 'p'
        assert label.is_active is True
    
    def test_label_validation(self, db_session, test_project):
        """Test label validation"""
        # Duplicate labels in same project
        label1 = Label(value='ORG', background='#00ff00', project_id=test_project.id)
        db_session.add(label1)
        db_session.commit()
        
        label2 = Label(value='ORG', background='#0000ff', project_id=test_project.id)
        db_session.add(label2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_label_methods(self, db_session, test_project):
        """Test label utility methods"""
        label = Label(
            value='LOCATION',
            background='#00ff00',
            hotkey='l',
            project_id=test_project.id
        )
        db_session.add(label)
        db_session.commit()
        
        # Test activation/deactivation
        label.deactivate()
        assert label.is_active is False
        
        label.activate()
        assert label.is_active is True
        
        # Test serialization
        result = label.to_dict()
        assert result['value'] == 'LOCATION'
        assert result['hotkey'] == 'l'


class TestServiceLayers:
    """Test service layer functionality"""
    
    @pytest.fixture
    def services(self, app):
        """Create service instances"""
        with app.app_context():
            yield {
                'user': UserService(),
                'project': ProjectService(),
                'task': TaskService(),
                'annotation': AnnotationService(),
                'label': LabelService()
            }
    
    def test_user_service(self, services, db_session):
        """Test UserService functionality"""
        user_service = services['user']
        
        # Test user creation
        user = user_service.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        assert user.username == 'testuser'
        assert user.check_password('password123')
        
        # Test user retrieval
        found_user = user_service.get_user_by_username('testuser')
        assert found_user is not None
        assert found_user.email == 'test@example.com'
        
        # Test authentication
        auth_user = user_service.authenticate('testuser', 'password123')
        assert auth_user is not None
        
        auth_fail = user_service.authenticate('testuser', 'wrongpassword')
        assert auth_fail is None
    
    def test_project_service(self, services, db_session):
        """Test ProjectService functionality"""
        user_service = services['user']
        project_service = services['project']
        
        # Create user first
        user = user_service.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Test project creation
        project = project_service.create_project(
            name='Test Project',
            description='Test description',
            owner_id=user.id
        )
        
        assert project.name == 'Test Project'
        assert project.owner_id == user.id
        
        # Test project retrieval
        projects = project_service.get_user_projects(user.id)
        assert len(projects) == 1
        assert projects[0].name == 'Test Project'
    
    def test_task_service(self, services, db_session):
        """Test TaskService functionality"""
        user_service = services['user']
        project_service = services['project']
        task_service = services['task']
        
        # Setup
        user = user_service.create_user('testuser', 'test@example.com', 'password')
        project = project_service.create_project('Test Project', 'Description', user.id)
        
        # Test task creation
        task = task_service.create_task(
            text='Apple Inc. is a technology company.',
            project_id=project.id
        )
        
        assert task.text == 'Apple Inc. is a technology company.'
        assert task.project_id == project.id
        
        # Test task retrieval
        tasks = task_service.get_project_tasks(project.id)
        assert len(tasks) == 1
        assert tasks[0].text == task.text
    
    def test_annotation_service(self, services, db_session):
        """Test AnnotationService functionality"""
        user_service = services['user']
        project_service = services['project']
        task_service = services['task']
        annotation_service = services['annotation']
        
        # Setup
        user = user_service.create_user('testuser', 'test@example.com', 'password')
        project = project_service.create_project('Test Project', 'Description', user.id)
        task = task_service.create_task('Google LLC was founded.', project.id)
        
        # Test annotation creation
        annotation = annotation_service.create_annotation(
            task_id=task.id,
            start=0,
            end=10,
            text='Google LLC',
            labels=['ORG']
        )
        
        assert annotation.text == 'Google LLC'
        assert annotation.labels == ['ORG']
        
        # Test annotation retrieval
        annotations = annotation_service.get_task_annotations(task.id)
        assert len(annotations) == 1
        assert annotations[0].text == 'Google LLC'
        
        # Test statistics
        stats = annotation_service.get_annotation_statistics(project.id)
        assert stats['total_annotations'] == 1


class TestDatabaseConstraints:
    """Test database constraints and edge cases"""
    
    def test_cascade_deletes(self, db_session):
        """Test cascade delete behavior"""
        # Create user and project
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db_session.add(user)
        db_session.commit()
        
        project = Project(name='Test Project', owner_id=user.id)
        db_session.add(project)
        db_session.commit()
        
        task = Task(text='Test task', project_id=project.id)
        db_session.add(task)
        db_session.commit()
        
        annotation = Annotation(
            start=0,
            end=4,
            text='Test',
            labels=['TEST'],
            task_id=task.id
        )
        db_session.add(annotation)
        db_session.commit()
        
        # Delete task should delete annotations
        db_session.delete(task)
        db_session.commit()
        
        remaining_annotations = db_session.query(Annotation).count()
        assert remaining_annotations == 0
    
    def test_large_text_handling(self, db_session):
        """Test handling of large text content"""
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db_session.add(user)
        db_session.commit()
        
        project = Project(name='Test Project', owner_id=user.id)
        db_session.add(project)
        db_session.commit()
        
        # Large text (10KB)
        large_text = 'A' * 10000
        task = Task(text=large_text, project_id=project.id)
        db_session.add(task)
        db_session.commit()
        
        assert len(task.text) == 10000
    
    def test_unicode_handling(self, db_session):
        """Test Unicode text handling"""
        user = User(username='testuser', email='test@example.com')
        user.set_password('password')
        db_session.add(user)
        db_session.commit()
        
        project = Project(name='Test Project', owner_id=user.id)
        db_session.add(project)
        db_session.commit()
        
        # Unicode text
        unicode_text = '这是中文测试 🌟 émojis and àccents'
        task = Task(text=unicode_text, project_id=project.id)
        db_session.add(task)
        db_session.commit()
        
        assert task.text == unicode_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])