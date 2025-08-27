"""
Configuration management for KDPII Labeler
Environment-based configuration with secure defaults
"""

import os
from pathlib import Path

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        # Handle postgres:// URLs for compatibility
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Default to SQLite
        basedir = Path(__file__).parent.parent.absolute()
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{basedir}/data/kdpii_labeler.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    # Session settings
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 7200  # 2 hours
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'data/uploads'
    ALLOWED_EXTENSIONS = {'jsonl', 'json', 'txt'}
    
    # Application settings
    ITEMS_PER_PAGE = 20
    DEFAULT_LABELS_FILE = 'config/default_labels.json'
    
    @staticmethod
    def init_app(app):
        """Initialize app-specific configuration"""
        # Ensure data directories exist
        os.makedirs('data', exist_ok=True)
        os.makedirs('data/uploads', exist_ok=True)
        os.makedirs('data/exports', exist_ok=True)
        os.makedirs('config', exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Override with more secure settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-must-set-secret-key-in-production'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to stderr in production
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}