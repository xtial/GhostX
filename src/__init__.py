"""Ghostx package"""

from flask import Flask
from flask_login import LoginManager
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta
import os
import logging
from logging.handlers import RotatingFileHandler
from .utils.log_sanitizer import create_safe_logger
from .database import db

# Initialize Flask extensions
login_manager = LoginManager()
csrf = CSRFProtect()
session = Session()

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        RotatingFileHandler(
            'logs/app.log',
            maxBytes=10000000,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

# Create safe logger instance for the application
logger = create_safe_logger('ghostx')

def create_app(test_config=None):
    app = Flask(__name__,
        static_folder='../static',
        template_folder='../templates'
    )
    
    if test_config is not None:
        # Load test config first
        app.config.update(test_config)
    else:
        # Load configuration
        from .config import Config
        app.config.from_object(Config)
        
        # Ensure database URI is set
        if 'SQLALCHEMY_DATABASE_URI' not in app.config:
            app.config['SQLALCHEMY_DATABASE_URI'] = app.config.get('DATABASE_URL', 'sqlite:///spoofer.db')
    
    # Ensure secret key is set
    app.secret_key = app.config['SECRET_KEY']
    
    # Session configuration
    app.config.update(
        SESSION_TYPE='filesystem',
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        WTF_CSRF_SECRET_KEY=app.config['SECRET_KEY']
    )
    
    # Initialize extensions with app
    db.init_app(app)
    csrf.init_app(app)
    session.init_app(app)
    login_manager.init_app(app)

    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Configure login manager
    login_manager.login_view = 'auth.login_page'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from .routes.auth import auth
    from .routes.admin import admin
    from .routes.admin_api import admin_api
    from .routes.main import main
    
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(admin_api, url_prefix='/api/admin')
    app.register_blueprint(main, url_prefix='/')
    
    # Set up logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/app.log',
            maxBytes=10240,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Ghostx startup')
    
    return app 