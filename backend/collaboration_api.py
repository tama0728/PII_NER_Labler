"""
API endpoints for team collaboration
"""

from flask import Blueprint, request, jsonify, session
from backend.services.collaboration_service import CollaborationService
import os
import json
import csv
from io import StringIO
from werkzeug.utils import secure_filename

collab_bp = Blueprint('collab', __name__)
collab_service = CollaborationService()

@collab_bp.route('/workspaces', methods=['GET'])
def list_workspaces():
    """List all available workspaces"""
    workspaces = collab_service.list_workspaces()
    return jsonify(workspaces)

@collab_bp.route('/workspaces', methods=['POST'])
def create_workspace():
    """Create a new workspace"""
    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return jsonify({'error': 'Workspace name is required'}), 400
    
    workspace_id = collab_service.create_workspace(name, description)
    return jsonify({
        'workspace_id': workspace_id,
        'message': f'Workspace "{name}" created successfully'
    })

@collab_bp.route('/workspaces/<workspace_id>', methods=['GET'])
def get_workspace(workspace_id):
    """Get workspace details"""
    workspace = collab_service.get_workspace(workspace_id)
    if not workspace:
        return jsonify({'error': 'Workspace not found'}), 404
    return jsonify(workspace)

@collab_bp.route('/workspaces/<workspace_id>', methods=['DELETE'])
def delete_workspace(workspace_id):
    """Delete a workspace"""
    success = collab_service.delete_workspace(workspace_id)
    if success:
        return jsonify({'message': 'Workspace deleted successfully'})
    return jsonify({'error': 'Workspace not found'}), 404

@collab_bp.route('/workspaces/<workspace_id>/join', methods=['POST'])
def join_workspace(workspace_id):
    """Join a workspace as a team member"""
    data = request.get_json()
    member_name = data.get('member_name')
    
    if not member_name:
        return jsonify({'error': 'Member name is required'}), 400
    
    success = collab_service.add_member_to_workspace(workspace_id, member_name)
    if not success:
        return jsonify({'error': 'Workspace not found'}), 404
    
    session['workspace_id'] = workspace_id
    session['member_name'] = member_name
    
    return jsonify({
        'message': f'Joined workspace as {member_name}',
        'workspace_id': workspace_id,
        'member_name': member_name
    })

@collab_bp.route('/workspaces/<workspace_id>/tasks', methods=['GET'])
def list_tasks(workspace_id):
    """List all tasks in a workspace"""
    workspace = collab_service.get_workspace(workspace_id)
    if not workspace:
        return jsonify({'error': 'Workspace not found'}), 404
    
    tasks = list(workspace.get('tasks', {}).values())
    return jsonify(tasks)

@collab_bp.route('/workspaces/<workspace_id>/tasks', methods=['POST'])
def create_task(workspace_id):
    """Create a new task in workspace"""
    data = request.get_json()
    text = data.get('text')
    metadata = data.get('metadata', {})
    
    if not text:
        return jsonify({'error': 'Task text is required'}), 400
    
    task_id = collab_service.add_task(workspace_id, text, metadata)
    if not task_id:
        return jsonify({'error': 'Failed to create task'}), 500
    
    return jsonify({
        'task_id': task_id,
        'message': 'Task created successfully'
    })

@collab_bp.route('/workspaces/<workspace_id>/tasks/<task_id>', methods=['GET'])
def get_task(workspace_id, task_id):
    """Get specific task details"""
    task = collab_service.get_task(workspace_id, task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task)

@collab_bp.route('/workspaces/<workspace_id>/tasks/<task_id>/annotate', methods=['POST'])
def annotate_task(workspace_id, task_id):
    """Add annotations to a task"""
    data = request.get_json()
    annotations = data.get('annotations', [])
    member_name = session.get('member_name') or data.get('member_name', 'Anonymous')
    
    success = collab_service.add_annotation(
        workspace_id, task_id, member_name, annotations
    )
    
    if not success:
        return jsonify({'error': 'Failed to save annotations'}), 500
    
    return jsonify({
        'message': 'Annotations saved successfully',
        'annotator': member_name
    })

@collab_bp.route('/workspaces/<workspace_id>/tasks/<task_id>/merge', methods=['GET'])
def merge_annotations(workspace_id, task_id):
    """Get merged annotations for a task"""
    strategy = request.args.get('strategy', 'union')
    
    merged = collab_service.merge_annotations(workspace_id, task_id, strategy)
    if merged is None:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify({
        'task_id': task_id,
        'merge_strategy': strategy,
        'merged_annotations': merged
    })

@collab_bp.route('/workspaces/<workspace_id>/export', methods=['GET'])
def export_workspace(workspace_id):
    """Export workspace data with merged annotations"""
    strategy = request.args.get('strategy', 'union')
    
    export_data = collab_service.export_workspace(workspace_id, strategy)
    if not export_data:
        return jsonify({'error': 'Workspace not found'}), 404
    
    return jsonify(export_data)

@collab_bp.route('/workspaces/<workspace_id>/statistics', methods=['GET'])
def get_statistics(workspace_id):
    """Get workspace statistics"""
    stats = collab_service.get_statistics(workspace_id)
    if not stats:
        return jsonify({'error': 'Workspace not found'}), 404
    
    return jsonify(stats)

@collab_bp.route('/workspaces/<workspace_id>/labels', methods=['GET'])
def get_labels(workspace_id):
    """Get workspace labels"""
    workspace = collab_service.get_workspace(workspace_id)
    if not workspace:
        return jsonify({'error': 'Workspace not found'}), 404
    
    labels = workspace.get('labels', [])
    return jsonify(labels)

@collab_bp.route('/workspaces/<workspace_id>/labels', methods=['POST'])
def add_label(workspace_id):
    """Add a new label to workspace"""
    workspace = collab_service.get_workspace(workspace_id)
    if not workspace:
        return jsonify({'error': 'Workspace not found'}), 404
    
    data = request.get_json()
    label_name = data.get('name')
    label_color = data.get('color', '#808080')
    
    if not label_name:
        return jsonify({'error': 'Label name is required'}), 400
    
    # Check if label already exists
    existing_labels = workspace.get('labels', [])
    for label in existing_labels:
        if label['name'] == label_name:
            return jsonify({'error': 'Label already exists'}), 400
    
    # Add new label
    new_label = {'name': label_name, 'color': label_color}
    workspace.setdefault('labels', []).append(new_label)
    collab_service.save_workspaces()
    
    return jsonify({
        'message': 'Label added successfully',
        'label': new_label
    })

# File upload configuration
ALLOWED_EXTENSIONS = {'txt', 'csv', 'json'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_file_content(file, filename):
    """Parse different file formats and extract texts"""
    texts = []
    file_extension = filename.rsplit('.', 1)[1].lower()
    
    try:
        content = file.read().decode('utf-8')
        
        if file_extension == 'txt':
            # Split by double newlines for paragraphs, or single newlines for sentences
            lines = content.strip().split('\n')
            texts = [line.strip() for line in lines if line.strip()]
            
        elif file_extension == 'csv':
            # Assume first column contains text data
            csv_reader = csv.reader(StringIO(content))
            headers = next(csv_reader, None)  # Skip header if exists
            
            # Try to detect text column
            text_column_idx = 0
            if headers:
                for i, header in enumerate(headers):
                    if any(keyword in header.lower() for keyword in ['text', 'content', 'sentence', 'document']):
                        text_column_idx = i
                        break
            
            for row in csv_reader:
                if len(row) > text_column_idx and row[text_column_idx].strip():
                    texts.append(row[text_column_idx].strip())
                    
        elif file_extension == 'json':
            # Support various JSON formats
            data = json.loads(content)
            
            if isinstance(data, list):
                # Array of texts or objects
                for item in data:
                    if isinstance(item, str):
                        texts.append(item.strip())
                    elif isinstance(item, dict):
                        # Look for common text fields
                        for key in ['text', 'content', 'sentence', 'document', 'message']:
                            if key in item and isinstance(item[key], str):
                                texts.append(item[key].strip())
                                break
                                
            elif isinstance(data, dict):
                # Single object or nested structure
                if 'texts' in data and isinstance(data['texts'], list):
                    texts = [str(t).strip() for t in data['texts'] if str(t).strip()]
                elif 'data' in data and isinstance(data['data'], list):
                    for item in data['data']:
                        if isinstance(item, str):
                            texts.append(item.strip())
                        elif isinstance(item, dict) and 'text' in item:
                            texts.append(str(item['text']).strip())
                else:
                    # Look for text fields in the object
                    for key in ['text', 'content', 'sentence', 'document']:
                        if key in data and isinstance(data[key], str):
                            texts.append(data[key].strip())
                            break
    
    except Exception as e:
        raise ValueError(f"Error parsing {file_extension} file: {str(e)}")
    
    return texts

@collab_bp.route('/workspaces/<workspace_id>/upload', methods=['POST'])
def upload_file(workspace_id):
    """Upload file and create tasks from content"""
    # Check if workspace exists
    workspace = collab_service.get_workspace(workspace_id)
    if not workspace:
        return jsonify({'error': 'Workspace not found'}), 404
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Supported: txt, csv, json'}), 400
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)     # Seek back to beginning
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large. Max size: 16MB'}), 400
    
    try:
        # Parse file content
        texts = parse_file_content(file, file.filename)
        
        if not texts:
            return jsonify({'error': 'No text content found in file'}), 400
        
        # Create tasks from parsed texts
        created_tasks = []
        failed_tasks = []
        
        for i, text in enumerate(texts):
            if len(text) < 5:  # Skip very short texts
                continue
                
            # Truncate very long texts
            if len(text) > 5000:
                text = text[:5000] + "..."
            
            task_id = collab_service.add_task(
                workspace_id, 
                text, 
                metadata={
                    'source': 'file_upload',
                    'filename': file.filename,
                    'line_number': i + 1
                }
            )
            
            if task_id:
                created_tasks.append(task_id)
            else:
                failed_tasks.append(i + 1)
        
        return jsonify({
            'message': f'File processed successfully',
            'filename': file.filename,
            'total_texts': len(texts),
            'created_tasks': len(created_tasks),
            'failed_tasks': len(failed_tasks),
            'task_ids': created_tasks
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to process file: {str(e)}'}), 500

@collab_bp.route('/workspaces/<workspace_id>/upload/batch', methods=['POST'])
def batch_upload(workspace_id):
    """Upload multiple files at once"""
    workspace = collab_service.get_workspace(workspace_id)
    if not workspace:
        return jsonify({'error': 'Workspace not found'}), 404
    
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    results = []
    total_created = 0
    
    for file in files:
        if file.filename == '':
            continue
            
        if not allowed_file(file.filename):
            results.append({
                'filename': file.filename,
                'status': 'error',
                'message': 'File type not allowed'
            })
            continue
        
        try:
            texts = parse_file_content(file, file.filename)
            created_tasks = []
            
            for i, text in enumerate(texts):
                if len(text) < 5:
                    continue
                    
                if len(text) > 5000:
                    text = text[:5000] + "..."
                
                task_id = collab_service.add_task(
                    workspace_id,
                    text,
                    metadata={
                        'source': 'batch_upload',
                        'filename': file.filename,
                        'line_number': i + 1
                    }
                )
                
                if task_id:
                    created_tasks.append(task_id)
            
            results.append({
                'filename': file.filename,
                'status': 'success',
                'created_tasks': len(created_tasks),
                'total_texts': len(texts)
            })
            
            total_created += len(created_tasks)
            
        except Exception as e:
            results.append({
                'filename': file.filename,
                'status': 'error',
                'message': str(e)
            })
    
    return jsonify({
        'message': f'Batch upload completed',
        'total_files': len(files),
        'total_created_tasks': total_created,
        'results': results
    })