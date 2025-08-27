#!/usr/bin/env python3
"""
KDPII Labeler - Main Flask Application
Entry point for the refactored NER annotation tool
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from backend.config import Config
from backend.database import db
from backend.auth import auth_bp
from backend.api import api_bp
import os

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__, 
                template_folder='../frontend/templates',
                static_folder='../frontend/static')
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        from backend.models.user import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from backend.views import views_bp
    app.register_blueprint(views_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        from backend.services.user_service import UserService
        user_service = UserService()
        user_service.create_default_admin()
    
    return app

def main():
    """Main entry point for console script"""
    app = create_app()
    
    print("Starting KDPII Labeler...")
    print("Refactored NER Annotation Tool")
    port = 8080
    print(f"Available at: http://localhost:{port}")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=port, threaded=True)
    except Exception as e:
        print(f"Error starting Flask app: {e}")
        raise

if __name__ == '__main__':
    main()