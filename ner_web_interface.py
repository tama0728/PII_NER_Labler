#!/usr/bin/env python3
"""
Label Studio NER Web Interface
Web interface for Named Entity Recognition based on Label Studio design
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
from ner_extractor import NERExtractor, NERLabel

app = Flask(__name__)

# Initialize extractor with error handling
try:
    extractor = NERExtractor()
    print(f"NERExtractor initialized with {len(extractor.labels)} labels")
except Exception as e:
    print(f"Error initializing NERExtractor: {e}")
    raise

# Static files
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/')
def index():
    """Main annotation interface"""
    try:
        print("Rendering index page...")
        labels = extractor.labels
        config_xml = extractor.get_label_config_xml()
        print(f"Rendering with {len(labels)} labels")
        
        return render_template('ner_interface.html', 
                             labels=labels,
                             config_xml=config_xml)
    except Exception as e:
        print(f"Error in index route: {e}")
        return f"Error loading interface: {str(e)}", 500

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new annotation task"""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    task_id = extractor.create_task(text)
    return jsonify({'task_id': task_id, 'text': text})

@app.route('/api/tasks/<task_id>')
def get_task(task_id):
    """Get task details"""
    task = extractor.get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify(task.to_dict())

@app.route('/api/tasks/<task_id>/annotations', methods=['POST'])
def add_annotation(task_id):
    """Add annotation to task"""
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

@app.route('/api/tasks/<task_id>/export')
def export_task(task_id):
    """Export task in Label Studio format"""
    try:
        exported = extractor.export_task(task_id)
        return jsonify(exported)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/tasks/<task_id>/conll')
def export_conll(task_id):
    """Export task in CoNLL format"""
    try:
        conll_data = extractor.export_conll_format(task_id)
        return jsonify({'conll': conll_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/statistics')
def get_statistics():
    """Get annotation statistics"""
    return jsonify(extractor.get_statistics())

@app.route('/api/config')
def get_config():
    """Get Label Studio XML configuration"""
    return {
        'basic_config': extractor.get_label_config_xml(),
        'enhanced_config': extractor.get_enhanced_config_xml(),
        'labels': [{'value': label.value, 'background': label.background, 'hotkey': label.hotkey} 
                  for label in extractor.labels]
    }

# Tag/Label CRUD API endpoints
@app.route('/api/tags', methods=['GET'])
def get_tags():
    """Get all tags/labels"""
    try:
        labels = extractor.get_all_labels()
        return jsonify(labels)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tags', methods=['POST'])
def create_tag():
    """Create a new tag/label"""
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

@app.route('/api/tags/<label_id>', methods=['GET'])
def get_tag(label_id):
    """Get a specific tag/label by ID"""
    try:
        label = extractor.get_label(label_id)
        if not label:
            return jsonify({'error': 'Tag not found'}), 404
        return jsonify(label)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tags/<label_id>', methods=['PUT'])
def update_tag(label_id):
    """Update an existing tag/label"""
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

@app.route('/api/tags/<label_id>', methods=['DELETE'])
def delete_tag(label_id):
    """Delete a tag/label"""
    try:
        result = extractor.delete_label(label_id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def main():
    """Main entry point for console script"""
    # Ensure static and templates directories exist
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Verify templates exist
    template_path = 'templates/ner_interface.html'
    if not os.path.exists(template_path):
        print(f"ERROR: Template file not found: {template_path}")
        return
    
    print("Starting NER Web Interface...")
    print("Based on Label Studio Named Entity Recognition functionality")
    port = 8080
    print(f"Available at: http://localhost:{port}")
    
    try:
        port = 8081
        print(f"Attempting to start on port {port}")
        app.run(debug=True, host='0.0.0.0', port=port, threaded=True)
    except Exception as e:
        print(f"Error starting Flask app: {e}")
        raise

if __name__ == '__main__':
    main()