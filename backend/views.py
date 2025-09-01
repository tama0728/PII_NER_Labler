"""
Main application views
Routes for serving the frontend
"""

from flask import Blueprint, render_template, session, redirect, url_for

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    """Main application page - redirect to collaboration"""
    return redirect('/collaborate')

@views_bp.route('/dashboard')
def dashboard():
    """User dashboard"""
    return render_template('dashboard.html')

@views_bp.route('/projects')
def projects():
    """Projects page"""  
    return render_template('dashboard.html')

@views_bp.route('/annotate')
def annotate():
    """Annotation interface"""
    return render_template('ner_interface.html')

@views_bp.route('/collaborate')
def collaborate():
    """Team collaboration page - no login required"""
    return render_template('collaborate.html')

@views_bp.route('/collaborate/workspace/<workspace_id>')
def workspace_annotate(workspace_id):
    """Workspace annotation interface with advanced NER features"""
    from flask import current_app
    session['workspace_id'] = workspace_id
    
    # Use the integrated NER extractor from app context
    try:
        extractor = current_app.ner_extractor
        labels = extractor.labels
        config_xml = extractor.get_label_config_xml()
        
        # Get member name from session (set when joining workspace)
        member_name = session.get('member_name', 'Anonymous')
        
        return render_template('ner_interface.html', 
                             workspace_id=workspace_id,
                             labels=labels,
                             config_xml=config_xml,
                             member_name=member_name)
    except Exception as e:
        print(f"Error loading workspace NER interface: {e}")
        return f"Error loading workspace NER interface: {str(e)}", 500