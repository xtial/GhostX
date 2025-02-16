"""Ghostx package"""

from flask import Flask, request, g, jsonify
from flask_login import LoginManager, current_user
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta
import os
import logging
from logging.handlers import RotatingFileHandler
from .utils.log_sanitizer import create_safe_logger
from .database import db
from src.utils.rate_limiter import RateLimiter
from src.models import APIRequest, SecurityLog
import time
from functools import wraps
from cachelib import RedisCache, SimpleCache
from flask_talisman import Talisman
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import threading
from werkzeug.middleware.proxy_fix import ProxyFix
import psutil
from src.config import Config
import werkzeug.exceptions
from src.utils.decorators import rate_limit_exempt

# Set up logging first
logger = create_safe_logger(__name__)

# Initialize Flask extensions
login_manager = LoginManager()
csrf = CSRFProtect()
session = Session()
compress = Compress()

# Initialize limiter with default config
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "200 per hour"],  # Increased default limits
    storage_uri=Config.REDIS_URL if hasattr(Config, 'REDIS_URL') else "memory://",
    strategy='fixed-window',  # Use fixed window strategy for better performance
    default_limits_exempt_when=lambda: (
        getattr(g, 'rate_limit_exempt', False) or
        (current_user and current_user.is_authenticated and current_user.is_admin) or
        (request.endpoint and (
            request.endpoint.startswith('admin_api') or
            request.endpoint.startswith('admin.') or
            'metrics' in request.endpoint.lower() or
            'stats' in request.endpoint.lower() or
            'security' in request.endpoint.lower() or  # Added security endpoints
            request.endpoint in [
                'static',
                'auth.login',
                'auth.login_page',
                'auth.logout',
                'auth.register',
                'main.index',
                'main.favicon',
                'health_check'
            ]
        ))
    ),
    headers_enabled=True,  # Enable rate limit headers
    retry_after='http-date',  # Use HTTP date format for retry-after header
    application_limits=["10000 per hour"]  # Global application limit
)

# Create rate limiter instance
rate_limiter = RateLimiter()

# System monitoring
system_stats = {
    'start_time': time.time(),
    'request_count': 0,
    'error_count': 0,
    'last_error_time': None,
    'active_users': set(),
    'peak_memory': 0,
    'peak_cpu': 0
}

# Initialize caching with fallback mechanism
cache = None
if hasattr(Config, 'REDIS_CONFIG') and Config.REDIS_CONFIG.get('enabled', False):
    try:
        cache = RedisCache(
            host=Config.REDIS_CONFIG.get('host', 'localhost'),
            port=Config.REDIS_CONFIG.get('port', 6379),
            password=Config.REDIS_CONFIG.get('password'),
            db=Config.REDIS_CONFIG.get('db', 0),
            default_timeout=300,
            key_prefix='ghostx:'
        )
        # Test Redis connection
        cache.set('test_key', 'test_value')
        test_value = cache.get('test_key')
        if test_value != 'test_value':
            raise Exception("Redis test key-value verification failed")
        logger.info("Redis cache initialized successfully")
    except Exception as e:
        logger.warning(f"Redis cache initialization failed, falling back to SimpleCache: {e}")
        cache = None

if cache is None:
    cache = SimpleCache()
    logger.info("Using SimpleCache for caching")

# Enhanced security headers
security_headers = {
    'default-src': "'self'",
    'script-src': "'self' 'unsafe-inline' 'unsafe-eval' cdnjs.cloudflare.com cdn.jsdelivr.net unpkg.com blob:",
    'style-src': "'self' 'unsafe-inline' fonts.googleapis.com cdnjs.cloudflare.com unpkg.com cdn.jsdelivr.net",
    'font-src': "'self' fonts.gstatic.com cdnjs.cloudflare.com",
    'img-src': "'self' data: blob: *",
    'frame-ancestors': "'none'",
    'base-uri': "'self'",
    'form-action': "'self'",
    'worker-src': "'self' blob:",
    'connect-src': "'self' blob:",
    'upgrade-insecure-requests': '',
    'block-all-mixed-content': ''
}

# Additional security headers to be added after response
additional_security_headers = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=(), payment=(), usb=(), battery=(), idle-detection=(), screen-wake-lock=(), web-share=()'
}

def monitor_system_resources():
    """Background thread to monitor system resources"""
    while True:
        try:
            # Update system statistics
            process = psutil.Process()
            system_stats['peak_memory'] = max(system_stats['peak_memory'], 
                                            process.memory_percent())
            system_stats['peak_cpu'] = max(system_stats['peak_cpu'], 
                                         process.cpu_percent())
            
            # Clean up expired sessions from active users
            current_time = time.time()
            for user_id in list(system_stats['active_users']):
                last_seen = cache.get(f'user_last_seen:{user_id}')
                if not last_seen or current_time - last_seen > 3600:
                    system_stats['active_users'].discard(user_id)
        except Exception as e:
            logger.error(f"Error in system monitoring: {e}")
        time.sleep(60)  # Update every minute

def create_app(test_config=None):
    app = Flask(__name__,
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
        static_url_path='/static',
        template_folder='../templates'
    )
    
    # Handle reverse proxies
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize security and performance enhancements
    Talisman(app, 
             content_security_policy=security_headers,
             force_https=not app.debug,
             strict_transport_security=True,
             session_cookie_secure=True)
    compress.init_app(app)
    
    # Initialize rate limiter
    from src.utils.rate_limiter import init_limiter
    init_limiter(app)
    
    # Start system monitoring in background
    if not app.debug and not app.testing:
        monitor_thread = threading.Thread(target=monitor_system_resources, daemon=True)
        monitor_thread.start()
    
    # Enhanced session configuration
    app.config.update(
        SESSION_TYPE='redis' if isinstance(cache, RedisCache) else 'filesystem',
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        SESSION_COOKIE_SECURE=not app.debug,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        WTF_CSRF_SECRET_KEY=app.config['SECRET_KEY'],
        # Performance optimizations
        SQLALCHEMY_ENGINE_OPTIONS={
            'pool_size': 20,
            'max_overflow': 40,
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_timeout': 20,
            'echo': app.debug
        },
        # Cache configuration
        CACHE_TYPE='redis' if isinstance(cache, RedisCache) else 'simple',
        CACHE_DEFAULT_TIMEOUT=300,
        # Security enhancements
        REMEMBER_COOKIE_SECURE=True,
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE='Lax',
        # Performance tuning
        PROPAGATE_EXCEPTIONS=True,
        PRESERVE_CONTEXT_ON_EXCEPTION=False,
        JSON_SORT_KEYS=False  # Better JSON performance
    )

    @app.before_request
    def update_request_stats():
        """Update request statistics"""
        system_stats['request_count'] += 1
        if current_user and current_user.is_authenticated:
            system_stats['active_users'].add(current_user.id)
            cache.set(f'user_last_seen:{current_user.id}', time.time(), timeout=3600)

    @app.errorhandler(Exception)
    def handle_error(error):
        """Global error handler"""
        try:
            system_stats['error_count'] += 1
            system_stats['last_error_time'] = time.time()
            
            # Log the error
            if hasattr(logger, 'exception'):
                logger.exception("Unhandled exception occurred")
            else:
                logger.error(f"Unhandled exception occurred: {str(error)}")
            
            # Handle 404 errors differently
            if isinstance(error, werkzeug.exceptions.NotFound):
                return jsonify({
                    'error': 'Not Found',
                    'message': 'The requested resource was not found'
                }), 404
                
            # Return appropriate error response
            return jsonify({
                'error': 'Internal server error',
                'message': str(error) if app.debug else 'An unexpected error occurred'
            }), 500
        except Exception as e:
            # Fallback error handling
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred'
            }), 500

    @app.route('/health')
    @rate_limit_exempt
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'uptime': time.time() - system_stats['start_time'],
            'requests': system_stats['request_count'],
            'errors': system_stats['error_count'],
            'active_users': len(system_stats['active_users']),
            'memory_usage': f"{system_stats['peak_memory']:.1f}%",
            'cpu_usage': f"{system_stats['peak_cpu']:.1f}%",
            'cache_type': 'redis' if isinstance(cache, RedisCache) else 'simple'
        })

    if test_config is not None:
        # Load test config first
        app.config.update(test_config)
    else:
        # Load configuration
        app.config.from_object(Config)
        
        # Ensure database URI is set
        if 'SQLALCHEMY_DATABASE_URI' not in app.config:
            app.config['SQLALCHEMY_DATABASE_URI'] = app.config.get('DATABASE_URL', 'sqlite:///spoofer.db')
    
    # Ensure secret key is set
    app.secret_key = app.config['SECRET_KEY']
    
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
    
    @app.before_request
    def check_rate_limit():
        """Check rate limits before processing any request"""
        try:
            # Skip processing if request is exempt
            if getattr(g, 'rate_limit_exempt', False):
                return

            if not request.endpoint:
                return
                
            # Define exempt paths and endpoints
            exempt_paths = {
                '/login', '/logout', '/register', '/', '/static', '/favicon.ico', 
                '/admin/metrics', '/admin/security', '/admin/status', '/admin/sessions',
                '/api/admin/metrics', '/api/admin/stats', '/api/stats', '/api/quota',
                '/api/limits', '/health', '/api/admin/security-metrics',  # Added security-metrics path
                '/admin/security-metrics'
            }
            exempt_endpoints = {
                'static', 'auth.login', 'auth.login_page', 'auth.logout', 'auth.register', 
                'main.index', 'main.favicon', 'auth.reset_password', 'auth.forgot_password',
                'admin_api.get_security_metrics', 'admin_api.get_system_status', 
                'admin_api.get_active_sessions', 'admin.get_user_permissions',
                'auth.logout_api', 'admin_api.update_metrics', 'admin_api.get_metrics',
                'admin.dashboard', 'main.get_limits', 'main.dashboard',
                'admin_api.get_stats', 'admin_api.get_quota', 'health_check',
                'admin_api.security_metrics', 'admin_api.security-metrics'  # Added security_metrics endpoint
            }
            
            # Skip rate limiting for exempt paths and endpoints
            if (request.path in exempt_paths or 
                any(request.path.startswith(path) for path in exempt_paths) or
                request.endpoint in exempt_endpoints):
                return
                
            # Skip rate limiting for admin users on admin endpoints
            if current_user and current_user.is_authenticated and current_user.is_admin:
                if request.endpoint and (
                    request.endpoint.startswith('admin') or 
                    request.endpoint.startswith('admin_api') or
                    'metrics' in request.endpoint.lower() or
                    'stats' in request.endpoint.lower()):
                    return

            # Skip rate limiting for unauthenticated users on public endpoints
            if not current_user or not current_user.is_authenticated:
                return

            # Use different rate limits for admin users
            if current_user.is_admin:
                rate_key = f'admin_rate_limit:{current_user.id}:{request.endpoint}'
                limit = cache.get(rate_key)
                if limit and limit > 2000:  # Much higher limit for admin users
                    return create_rate_limit_response()
            else:
                # Check cached rate limit status with shorter TTL for high-traffic endpoints
                cache_key = f'rate_limit:{current_user.id}:{request.endpoint}'
                is_rate_limited = cache.get(cache_key)
                
                if is_rate_limited:
                    return create_rate_limit_response()
                
                # Check rate limits with different thresholds for different endpoint types
                if 'api' in request.endpoint:
                    if not rate_limiter.check_rate_limit(current_user.id, limit=200):  # Higher limit for API endpoints
                        ttl = 60
                        cache.set(cache_key, True, timeout=ttl)
                        return create_rate_limit_response()
                else:
                    if not rate_limiter.check_rate_limit(current_user.id):
                        ttl = 300
                        cache.set(cache_key, True, timeout=ttl)
                        return create_rate_limit_response()
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            return None  # Continue processing request on error

    def create_rate_limit_response():
        """Create a standardized rate limit exceeded response"""
        try:
            # Log rate limit violation
            log = SecurityLog(
                title='Rate Limit Exceeded',
                message=f'User {current_user.username} exceeded rate limit for endpoint {request.endpoint}',
                severity='medium',
                user_id=current_user.id,
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            # Get quota information
            quota = rate_limiter.get_remaining_quota(current_user.id)
            response = jsonify({
                'success': False,
                'message': 'Rate limit exceeded. Please try again later.',
                'quota': quota,
                'retry_after': quota['hourly']['reset_in'] if quota else 3600
            })
            response.status_code = 429
            
            # Add standard rate limit headers
            if quota:
                response.headers.update({
                    'X-RateLimit-Limit': str(quota['hourly']['limit']),
                    'X-RateLimit-Remaining': str(quota['hourly']['remaining']),
                    'X-RateLimit-Reset': str(quota['hourly']['reset_in']),
                    'Retry-After': str(quota['hourly']['reset_in'])
                })
            
            return response
        except Exception as e:
            logger.error(f"Error creating rate limit response: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    @app.after_request
    def add_rate_limit_headers(response):
        """Add rate limit headers to all responses"""
        if current_user and current_user.is_authenticated and not getattr(g, 'rate_limit_exempt', False):
            try:
                quota = rate_limiter.get_remaining_quota(current_user.id)
                if quota:
                    response.headers.update({
                        'X-RateLimit-Limit': str(quota['hourly']['limit']),
                        'X-RateLimit-Remaining': str(quota['hourly']['remaining']),
                        'X-RateLimit-Reset': str(quota['hourly']['reset_in'])
                    })
            except Exception as e:
                logger.error(f"Error adding rate limit headers: {str(e)}")
        return response

    @app.before_request
    def track_api_usage():
        """Track API usage for monitoring"""
        if not request.endpoint or request.endpoint.startswith('static'):
            return
            
        if current_user and current_user.is_authenticated:
            try:
                api_request = APIRequest(
                    user_id=current_user.id,
                    endpoint=request.endpoint,
                    method=request.method,
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string,
                    response_time=None
                )
                g.start_time = time.time()
                g.api_request = api_request
                db.session.add(api_request)
                db.session.commit()
            except Exception as e:
                logger.error(f"Error tracking API usage: {str(e)}")

    @app.after_request
    def update_api_metrics(response):
        """Update API request metrics"""
        try:
            if hasattr(g, 'start_time') and hasattr(g, 'api_request'):
                g.api_request.response_time = time.time() - g.start_time
                g.api_request.status_code = response.status_code
                db.session.commit()
        except Exception as e:
            logger.error(f"Error updating API metrics: {str(e)}")
        return response

    @app.after_request
    def add_security_headers(response):
        """Add additional security headers"""
        for header, value in additional_security_headers.items():
            response.headers[header] = value
        return response

    @app.after_request
    def add_header(response):
        if 'Cache-Control' not in response.headers:
            response.headers['Cache-Control'] = 'no-store'
        return response

    return app 