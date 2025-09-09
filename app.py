#!/usr/bin/env python3
"""
KDPII Labeler - Integrated NER + Backend Application
Main entry point combining ner_web_interface.py features with backend architecture
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect
from flask_sqlalchemy import SQLAlchemy
from backend.config import Config
from backend.database import db
from backend.api import api_bp
import os
from datetime import datetime

# Import NER functionality (core feature)
from ner_extractor import NERExtractor

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__, 
                template_folder='frontend/templates',
                static_folder='frontend/static')
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from backend.views import views_bp
    from backend.collaboration_api import collab_bp
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(collab_bp, url_prefix='/collab')
    
    # Initialize NER extractor
    try:
        extractor = NERExtractor()
        print(f"NERExtractor initialized with {len(extractor.labels)} labels")
        app.ner_extractor = extractor  # Store in app context
    except Exception as e:
        
        print(f"Error initializing NERExtractor: {e}")
        raise

    # Add NER routes from ner_web_interface.py
    
    # Redirect root access to collaboration interface
    @app.route('/ner')
    def ner_redirect():
        """Redirect to collaboration interface"""
        return redirect('/collaborate')
    
    # NER API routes - Original paths for workspace_ner_interface.html compatibility
    @app.route('/api/tasks', methods=['POST'])
    def ner_create_task_original():
        """Create a new NER annotation task (original path)"""
        return ner_create_task()

    # NER API routes - Tasks (using /api/ner prefix to avoid conflicts)
    @app.route('/api/ner/tasks', methods=['POST'])
    def ner_create_task():
        """Create a new NER annotation task"""
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        task_id = extractor.create_task(text)
        return jsonify({'task_id': task_id, 'text': text})

    @app.route('/api/ner/tasks/<task_id>')
    def ner_get_task(task_id):
        """Get NER task details"""
        task = extractor.get_task(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify(task.to_dict())

    @app.route('/api/ner/tasks/<task_id>/annotations', methods=['POST'])
    def ner_add_annotation(task_id):
        """Add annotation to NER task"""
        data = request.json
        
        try:
            annotation_id = extractor.add_annotation(
                task_id,
                data['start'],
                data['end'], 
                data['labels']
            )
            return jsonify({'annotation_id': annotation_id})
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/ner/tasks/<task_id>/export')
    def ner_export_task(task_id):
        """Export NER task in Label Studio format"""
        try:
            exported = extractor.export_task(task_id)
            return jsonify(exported)
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/ner/tasks/<task_id>/conll')
    def ner_export_conll(task_id):
        """Export NER task in CoNLL format"""
        try:
            conll_data = extractor.export_conll_format(task_id)
            return jsonify({'conll': conll_data})
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/ner/statistics')
    def ner_get_statistics():
        """Get NER annotation statistics"""
        return jsonify(extractor.get_statistics())

    @app.route('/api/ner/config')
    def ner_get_config():
        """Get NER Label Studio XML configuration"""
        return {
            'basic_config': extractor.get_label_config_xml(),
            'enhanced_config': extractor.get_enhanced_config_xml(),
            'labels': [{'value': label.value, 'background': label.background, 'hotkey': label.hotkey} 
                      for label in extractor.labels]
        }

    # NER Tag/Label CRUD API endpoints
    @app.route('/api/ner/tags', methods=['GET'])
    def ner_get_tags():
        """Get all NER tags/labels"""
        try:
            labels = extractor.get_all_labels()
            return jsonify(labels)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/ner/tags', methods=['POST'])
    def ner_create_tag():
        """Create a new NER tag/label"""
        data = request.json
        
        if not data or not data.get('value'):
            return jsonify({'error': 'Tag value is required'}), 400
        
        try:
            label_id = extractor.create_label(
                value=data['value'],
                background=data.get('background', '#999999'),
                hotkey=data.get('hotkey'),
                category=data.get('category'),
                description=data.get('description'),
                example=data.get('example')
            )
            created_label = extractor.get_label(label_id)
            return jsonify(created_label), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/ner/tags/<label_id>', methods=['GET'])
    def ner_get_tag(label_id):
        """Get a specific NER tag/label by ID"""
        try:
            label = extractor.get_label(label_id)
            if not label:
                return jsonify({'error': 'Tag not found'}), 404
            return jsonify(label)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/ner/tags/<label_id>', methods=['PUT'])
    def ner_update_tag(label_id):
        """Update an existing NER tag/label"""
        data = request.json
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        try:
            updated_label = extractor.update_label(
                label_id=label_id,
                value=data.get('value'),
                background=data.get('background'),
                hotkey=data.get('hotkey'),
                category=data.get('category'),
                description=data.get('description'),
                example=data.get('example')
            )
            return jsonify(updated_label)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/ner/tags/<label_id>', methods=['DELETE'])
    def ner_delete_tag(label_id):
        """Delete a NER tag/label"""
        try:
            result = extractor.delete_label(label_id)
            return jsonify(result)
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Original API routes for workspace_ner_interface.html compatibility
    @app.route('/api/tasks/<task_id>')
    def ner_get_task_original(task_id):
        return ner_get_task(task_id)

    @app.route('/api/tasks/<task_id>/annotations', methods=['POST'])
    def ner_add_annotation_original(task_id):
        return ner_add_annotation(task_id)

    @app.route('/api/tasks/<task_id>/export')
    def ner_export_task_original(task_id):
        return ner_export_task(task_id)

    @app.route('/api/tasks/<task_id>/conll')
    def ner_export_conll_original(task_id):
        return ner_export_conll(task_id)

    @app.route('/api/statistics')
    def ner_get_statistics_original():
        return ner_get_statistics()

    @app.route('/api/config')
    def ner_get_config_original():
        return ner_get_config()

    @app.route('/api/tags', methods=['GET'])
    def ner_get_tags_original():
        return ner_get_tags()

    @app.route('/api/tags', methods=['POST'])
    def ner_create_tag_original():
        return ner_create_tag()

    @app.route('/api/tags/<label_id>', methods=['GET'])
    def ner_get_tag_original(label_id):
        return ner_get_tag(label_id)

    @app.route('/api/tags/<label_id>', methods=['PUT'])
    def ner_update_tag_original(label_id):
        return ner_update_tag(label_id)

    @app.route('/api/tags/<label_id>', methods=['DELETE'])
    def ner_delete_tag_original(label_id):
        return ner_delete_tag(label_id)

    # Export file management endpoints for dashboard
    @app.route('/api/exports', methods=['GET'])
    def get_exports():
        """Get list of exported files with actual workspace names"""
        try:
            files = []
            exports_dir = os.path.join(os.getcwd(), 'exports')
            
            # Load workspace names - use hardcoded for now
            workspace_names = {
                '297048ca': 'test1',
                '12f6dd45': 'test2'
            }
            print(f"🏷️ 하드코딩된 워크스페이스 매핑: {workspace_names}")
            
            # Try to load from collaboration service as backup
            try:
                from backend.services.collaboration_service import CollaborationService
                collab_service = CollaborationService()
                workspaces = collab_service.list_workspaces()
                print(f"🗂️ 로드된 워크스페이스: {workspaces}")
                if workspaces:
                    for workspace in workspaces:
                        workspace_names[workspace['id']] = workspace['name']
                    print(f"🏷️ 업데이트된 워크스페이스 매핑: {workspace_names}")
            except Exception as e:
                print(f"❌ 워크스페이스 로딩 실패, 하드코딩 사용: {e}")
                import traceback
                traceback.print_exc()
            
            # Check both modified and completed directories
            for subdir in ['modified', 'completed']:
                subdir_path = os.path.join(exports_dir, subdir)
                if os.path.exists(subdir_path):
                    for filename in os.listdir(subdir_path):
                        if filename.endswith('.jsonl'):
                            file_path = os.path.join(subdir_path, filename)
                            stat = os.stat(file_path)
                            
                            # Parse new filename format: {workspace_name}_{annotator_name}_{base}_completed_{timestamp}.jsonl
                            workspace_name = subdir.capitalize()  # fallback
                            annotator_name = 'unknown_user'  # fallback
                            
                            # Try to parse the new filename format
                            if filename.count('_') >= 4:  # workspace_annotator_base_completed_timestamp.jsonl
                                parts = filename.replace('.jsonl', '').split('_')
                                if len(parts) >= 5 and 'completed' in parts:
                                    workspace_name = parts[0]
                                    annotator_name = parts[1]
                            else:
                                # Fallback: try old logic for existing files
                                for ws_id, ws_name in workspace_names.items():
                                    if ws_id in filename or ws_name.lower() in filename.lower():
                                        workspace_name = ws_name
                                        break
                            
                            files.append({
                                'id': f"{subdir}_{filename}",
                                'name': filename,
                                'workspace': workspace_name,
                                'annotator': annotator_name,
                                'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                'size': stat.st_size,
                                'format': 'jsonl',
                                'record_count': 'N/A'
                            })
            files.sort(key=lambda x: x['created_at'], reverse=True)
            return jsonify({'files': files})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/exports/<file_id>/download', methods=['GET'])
    def download_export(file_id):
        """Download exported file"""
        try:
            # Parse file_id (format: "subdir_filename")
            parts = file_id.split('_', 1)
            if len(parts) != 2:
                return jsonify({'error': 'Invalid file ID'}), 400
            
            subdir, filename = parts
            exports_dir = os.path.join(os.getcwd(), 'exports')
            file_path = os.path.join(exports_dir, subdir.lower(), filename)
            
            if not os.path.exists(file_path):
                return jsonify({'error': 'File not found'}), 404
            
            return send_from_directory(
                os.path.join(exports_dir, subdir.lower()), 
                filename, 
                as_attachment=True
            )
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/exports/<file_id>/preview', methods=['GET'])
    def preview_export(file_id):
        """Preview exported file content"""
        try:
            # Parse file_id (format: "subdir_filename")
            parts = file_id.split('_', 1)
            if len(parts) != 2:
                return jsonify({'error': 'Invalid file ID'}), 400
            
            subdir, filename = parts
            exports_dir = os.path.join(os.getcwd(), 'exports')
            file_path = os.path.join(exports_dir, subdir.lower(), filename)
            
            if not os.path.exists(file_path):
                return jsonify({'error': 'File not found'}), 404
            
            # Read raw file content for JSONL display
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/exports/<file_id>', methods=['DELETE'])
    def delete_export(file_id):
        """Delete exported file"""
        try:
            # Parse file_id (format: "subdir_filename")
            parts = file_id.split('_', 1)
            if len(parts) != 2:
                return jsonify({'error': 'Invalid file ID'}), 400
            
            subdir, filename = parts
            exports_dir = os.path.join(os.getcwd(), 'exports')
            file_path = os.path.join(exports_dir, subdir.lower(), filename)
            
            if not os.path.exists(file_path):
                return jsonify({'error': 'File not found'}), 404
            
            os.remove(file_path)
            return jsonify({'message': 'File deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # File save endpoints
    @app.route('/api/save-modified-file', methods=['POST'])
    def save_modified_file():
        """Save modified/preprocessed file to server"""
        try:
            data = request.json
            filename = data.get('filename', 'modified_file.jsonl')
            content = data.get('content', '')
            
            if not content:
                return jsonify({'error': 'No content provided'}), 400
            
            # Create exports/modified directory if it doesn't exist
            exports_dir = os.path.join(os.getcwd(), 'exports')
            modified_dir = os.path.join(exports_dir, 'modified')
            os.makedirs(modified_dir, exist_ok=True)
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = filename.replace('.jsonl', '')
            save_filename = f"{base_name}_modified_{timestamp}.jsonl"
            file_path = os.path.join(modified_dir, save_filename)
            
            # Save file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return jsonify({
                'success': True,
                'filename': save_filename,
                'filepath': file_path,
                'message': f'수정된 파일이 서버에 저장되었습니다: {save_filename}'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/save-completed-file', methods=['POST'])
    def save_completed_file():
        """Save completed/labeled file to server"""
        try:
            data = request.json
            filename = data.get('filename', 'completed_file.jsonl')
            content = data.get('content', '')
            
            if not content:
                return jsonify({'error': 'No content provided'}), 400
            
            # Get workspace info from session
            workspace_id = session.get('workspace_id', 'unknown')
            member_name = session.get('member_name', 'unknown_user')
            
            # Get workspace name from CollaborationService
            workspace_name = 'unknown_workspace'
            try:
                from backend.services.collaboration_service import CollaborationService
                collab_service = CollaborationService()
                workspaces = collab_service.list_workspaces()
                for workspace in workspaces:
                    if workspace['id'] == workspace_id:
                        workspace_name = workspace['name']
                        break
            except Exception as e:
                print(f"⚠️ 워크스페이스 이름 조회 실패: {e}")
            
            # Create exports/completed directory if it doesn't exist
            exports_dir = os.path.join(os.getcwd(), 'exports')
            completed_dir = os.path.join(exports_dir, 'completed')
            os.makedirs(completed_dir, exist_ok=True)
            
            # Generate unique filename with workspace and annotator info
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = filename.replace('.jsonl', '')
            save_filename = f"{workspace_name}_{member_name}_{base_name}_completed_{timestamp}.jsonl"
            file_path = os.path.join(completed_dir, save_filename)
            
            # Save file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return jsonify({
                'success': True,
                'filename': save_filename,
                'filepath': file_path,
                'workspace': workspace_name,
                'annotator': member_name,
                'message': f'완성된 파일이 서버에 저장되었습니다: {save_filename}'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Create database tables
    with app.app_context():
        db.create_all()
    
    return app

def main():
    """Main entry point for console script"""
    app = create_app()
    
    print("Starting KDPII Labeler...")
    print("Integrated NER + Backend Server")
    port = 8080
    print(f"Available at: http://localhost:{port}")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=port, threaded=True)
    except Exception as e:
        print(f"Error starting Flask app: {e}")
        raise

if __name__ == '__main__':
    main()