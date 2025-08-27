"""
Main application views
Routes for serving the frontend
"""

from flask import Blueprint, render_template
from flask_login import login_required

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    """Main application page"""
    return render_template('dashboard.html')

@views_bp.route('/dashboard')
@login_required  
def dashboard():
    """User dashboard"""
    return render_template('dashboard.html')

@views_bp.route('/projects')
@login_required
def projects():
    """Projects page"""  
    return render_template('dashboard.html')

@views_bp.route('/annotate')
@login_required
def annotate():
    """Annotation interface"""
    return render_template('ner_interface.html')