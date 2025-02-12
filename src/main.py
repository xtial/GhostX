import logging
import sys
import json
import traceback
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, send_from_directory, request, jsonify, session, redirect, url_for
from functools import wraps
from .config import Config
from .utils.rate_limiter import limiter
from .routes.auth import auth
from .routes.admin import admin
from .routes.main import main
from .models import db, User
from pathlib import Path
from flask_session import Session
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='logs/app.log'
)
logger = logging.getLogger(__name__)

# Required directories and files
REQUIRED_DIRS = [
    'static/templates',
    'static/css',
    'static/js',
    'static/img',
    'database/data',
    'logs',
    'data'
]

# Create required directories
for dir_path in REQUIRED_DIRS:
    try:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created/verified directory: {dir_path}")
    except Exception as e:
        logger.error(f"Failed to create directory {dir_path}: {e}")

REQUIRED_FILES = [
    ('static/css/style.css', 'Default stylesheet not found'),
    ('static/js/main.js', 'Main JavaScript file not found'),
    ('templates/index.html', 'Login page template not found'),
    ('templates/dashboard.html', 'Dashboard template not found'),
    ('templates/404.html', '404 error page not found')
]

def check_required_files():
    """Check if all required files and directories exist"""
    missing_items = []
    
    # Check directories
    for dir_path in REQUIRED_DIRS:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
                logging.info(f"Created directory: {dir_path}")
            except Exception as e:
                missing_items.append(f"Failed to create directory {dir_path}: {str(e)}")
    
    # Check files
    for file_path, error_msg in REQUIRED_FILES:
        if not os.path.exists(file_path):
            missing_items.append(f"{error_msg} ({file_path})")
    
    return missing_items

# Initialize Flask-Login
login_manager = LoginManager()

def create_app():
    # Initialize Flask app
    app = Flask(__name__,
        static_folder='../static',
        template_folder='../templates'
    )
    
    # Load configuration
    app.config.from_object(Config)
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', os.urandom(32)),
        SESSION_TYPE='filesystem',
        SESSION_FILE_DIR='sessions',
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        JSON_SORT_KEYS=False,
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_SECRET_KEY=os.environ.get('CSRF_SECRET_KEY', os.urandom(32)),
        DEBUG=True,
        TESTING=True,
        PROPAGATE_EXCEPTIONS=True
    )

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    csrf = CSRFProtect(app)
    Session(app)
    limiter.init_app(app)
    
    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login_page'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints AFTER login manager initialization
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/api')
    app.register_blueprint(admin)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    # Set up logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
            
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Ghostx startup')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False) 