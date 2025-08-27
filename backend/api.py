"""
Main API blueprint - simplified implementation
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend.services import (
    ProjectService, TaskService, AnnotationService, 
    LabelService, DataImportService
)

api_bp = Blueprint('api', __name__)

# Initialize services
project_service = ProjectService()
task_service = TaskService()
annotation_service = AnnotationService()
label_service = LabelService()
data_import_service = DataImportService()

# Projects endpoints
@api_bp.route('/projects', methods=['GET'])
@login_required
def get_projects():
    """Get user's projects"""
    projects = project_service.get_user_projects(current_user.id)
    return jsonify([p.to_dict(include_stats=True) for p in projects])

@api_bp.route('/projects', methods=['POST'])
@login_required
def create_project():
    """Create new project"""
    data = request.get_json()
    print(f"DEBUG: Received project creation data: {data}")
    print(f"DEBUG: Current user: {current_user.username}, role: {current_user.role}")
    try:
        project = project_service.create_project(
            name=data.get('name'),
            owner_id=current_user.id,
            description=data.get('description')
        )
        print(f"DEBUG: Successfully created project: {project.name}")
        return jsonify(project.to_dict()), 201
    except ValueError as e:
        print(f"DEBUG: Project creation failed: {str(e)}")
        return jsonify({'error': str(e)}), 400

@api_bp.route('/projects/<int:project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    """Get project details"""
    project_data = project_service.get_project_dashboard_data(project_id, current_user.id)
    if not project_data:
        return jsonify({'error': 'Project not found'}), 404
    return jsonify(project_data)

# Tasks endpoints
@api_bp.route('/projects/<int:project_id>/tasks', methods=['GET'])
@login_required
def get_project_tasks(project_id):
    """Get tasks for project"""
    tasks = task_service.get_project_tasks(project_id, current_user.id)
    return jsonify([t.to_dict() for t in tasks])

@api_bp.route('/projects/<int:project_id>/tasks', methods=['POST'])
@login_required
def create_task(project_id):
    """Create new task"""
    data = request.get_json()
    try:
        if 'texts' in data:  # Bulk create
            tasks = task_service.bulk_create_tasks(
                project_id, data['texts'], current_user.id
            )
            return jsonify([t.to_dict() for t in tasks]), 201
        else:  # Single task
            task = task_service.create_task(
                project_id, data.get('text'), current_user.id
            )
            return jsonify(task.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

# Annotations endpoints
@api_bp.route('/tasks/<int:task_id>/annotations', methods=['POST'])
@login_required
def create_annotation(task_id):
    """Create annotation"""
    data = request.get_json()
    try:
        annotation = annotation_service.create_annotation(
            task_id=task_id,
            start=data.get('start'),
            end=data.get('end'),
            text=data.get('text'),
            labels=data.get('labels', []),
            user_id=current_user.id,
            confidence=data.get('confidence', 'high')
        )
        return jsonify(annotation.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/tasks/<int:task_id>/annotations', methods=['GET'])
@login_required
def get_task_annotations(task_id):
    """Get task annotations"""
    annotations = annotation_service.get_task_annotations(task_id, current_user.id)
    return jsonify([a.to_dict() for a in annotations])

# Labels endpoints
@api_bp.route('/projects/<int:project_id>/labels', methods=['GET'])
@login_required
def get_project_labels(project_id):
    """Get project labels"""
    labels = label_service.get_project_labels(project_id, current_user.id)
    return jsonify([l.to_dict() for l in labels])

@api_bp.route('/projects/<int:project_id>/labels', methods=['POST'])
@login_required
def create_label(project_id):
    """Create label"""
    data = request.get_json()
    try:
        label = label_service.create_label(
            project_id, data.get('value'), current_user.id, **data
        )
        return jsonify(label.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

# Data import endpoint
@api_bp.route('/projects/<int:project_id>/import', methods=['POST'])
@login_required
def import_data(project_id):
    """Import JSONL data"""
    data = request.get_json()
    try:
        result = data_import_service.import_jsonl_data(
            project_id, data.get('jsonl_data'), current_user.id
        )
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

# Advanced NER API endpoints (GitHub integration)
@api_bp.route('/config', methods=['GET'])
@login_required
def get_config():
    """Get Label Studio XML configuration"""
    from ner_extractor import NERExtractor
    extractor = NERExtractor()
    return jsonify({
        'basic_config': extractor.get_label_config_xml(),
        'enhanced_config': extractor.get_enhanced_config_xml(),
        'labels': [{'value': label.value, 'background': label.background, 'hotkey': label.hotkey} 
                  for label in extractor.labels]
    })

@api_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """Get annotation statistics"""
    # TODO: Implement project-specific statistics
    return jsonify({
        'total_annotations': 0,
        'labels_distribution': {},
        'completion_rate': 0.0
    })

@api_bp.route('/tasks/<int:task_id>/export', methods=['GET'])
@login_required  
def export_task(task_id):
    """Export task in Label Studio format"""
    try:
        task = task_service.get_task_by_id(task_id, current_user.id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Convert to Label Studio format
        ls_format = {
            'id': task.id,
            'data': {'text': task.text},
            'annotations': []
        }
        
        for annotation in task.annotations:
            ls_annotation = {
                'id': annotation.id,
                'result': [{
                    'from_name': 'label',
                    'to_name': 'text', 
                    'type': 'labels',
                    'value': {
                        'start': annotation.start,
                        'end': annotation.end,
                        'text': annotation.text,
                        'labels': annotation.labels.split(',') if annotation.labels else []
                    }
                }]
            }
            ls_format['annotations'].append(ls_annotation)
            
        return jsonify(ls_format)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/tasks/<int:task_id>/conll', methods=['GET'])
@login_required
def export_conll(task_id):
    """Export task in CoNLL format"""
    try:
        task = task_service.get_task_by_id(task_id, current_user.id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
            
        # Simple CoNLL format generation
        conll_lines = []
        tokens = task.text.split()
        
        for i, token in enumerate(tokens):
            # Simple B-I-O tagging (this should be improved)
            tag = 'O'  # Default outside
            
            # Check if token is part of any annotation
            for annotation in task.annotations:
                if annotation.start <= task.text.find(token) < annotation.end:
                    labels = annotation.labels.split(',') if annotation.labels else ['MISC']
                    tag = f'B-{labels[0]}' if i == 0 else f'I-{labels[0]}'
                    break
                    
            conll_lines.append(f'{token}\t{tag}')
        
        return jsonify({'conll': '\n'.join(conll_lines)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Individual label management
@api_bp.route('/projects/<int:project_id>/labels/<int:label_id>', methods=['GET'])
@login_required
def get_label(project_id, label_id):
    """Get specific label"""
    try:
        label = label_service.get_label_by_id(label_id, current_user.id)
        if not label:
            return jsonify({'error': 'Label not found'}), 404
        return jsonify(label.to_dict())
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/projects/<int:project_id>/labels/<int:label_id>', methods=['PUT'])
@login_required
def update_label(project_id, label_id):
    """Update existing label"""
    data = request.get_json()
    try:
        label = label_service.update_label(
            label_id, current_user.id, **data
        )
        if not label:
            return jsonify({'error': 'Label not found'}), 404
        return jsonify(label.to_dict())
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/projects/<int:project_id>/labels/<int:label_id>', methods=['DELETE'])
@login_required
def delete_label(project_id, label_id):
    """Delete label"""
    try:
        success = label_service.delete_label(label_id, current_user.id)
        if not success:
            return jsonify({'error': 'Label not found'}), 404
        return jsonify({'message': 'Label deleted successfully'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400