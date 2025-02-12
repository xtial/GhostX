from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy import func, text
from src.models import db, Session, LoginAttempt, APIRequest
import psutil
import smtplib
import requests
import logging

logger = logging.getLogger(__name__)

# Shared password context for consistent hashing across the application
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generate a password hash."""
    return pwd_context.hash(password)

def check_system_status():
    """Check the status of various system components"""
    status = {
        'api': 'normal',
        'database': 'normal',
        'email': 'normal'
    }
    
    try:
        # Check API health
        api_errors = APIRequest.query.filter(
            APIRequest.status_code >= 500,
            APIRequest.timestamp >= datetime.utcnow() - timedelta(minutes=5)
        ).count()
        
        if api_errors > 10:
            status['api'] = 'error'
        elif api_errors > 5:
            status['api'] = 'warning'
            
        # Check database health
        try:
            db.session.execute(text('SELECT 1'))
            db.session.commit()
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            status['database'] = 'error'
            
        # Check system resources
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent > 90 or memory_percent > 90:
            status['api'] = 'error'
        elif cpu_percent > 75 or memory_percent > 75:
            status['api'] = 'warning'
            
        # Check email service
        try:
            smtp = smtplib.SMTP(timeout=5)
            smtp.connect('smtp.gmail.com', 587)
            smtp.quit()
        except Exception as e:
            logger.error(f"Email service check failed: {str(e)}")
            status['email'] = 'error'
            
    except Exception as e:
        logger.error(f"Error checking system status: {str(e)}")
        for key in status:
            status[key] = 'error'
            
    return status

def track_login_attempt(username, ip_address, user_agent, success):
    """Track a login attempt"""
    try:
        attempt = LoginAttempt(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
        db.session.add(attempt)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error tracking login attempt: {str(e)}")
        db.session.rollback()

def track_api_request(endpoint, method, user_id, ip_address, status_code):
    """Track an API request"""
    try:
        request = APIRequest(
            endpoint=endpoint,
            method=method,
            user_id=user_id,
            ip_address=ip_address,
            status_code=status_code
        )
        db.session.add(request)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error tracking API request: {str(e)}")
        db.session.rollback()

def get_active_sessions(minutes=30):
    """Get active sessions within the specified time window"""
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return Session.query.filter(Session.last_active >= cutoff).all()
    except Exception as e:
        logger.error(f"Error getting active sessions: {str(e)}")
        return []

def get_security_metrics(hours=1):
    """Get security metrics for the specified time window"""
    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        # Get login attempts
        login_attempts = db.session.query(
            func.strftime('%Y-%m-%d %H:%M', LoginAttempt.timestamp).label('interval'),
            func.count(LoginAttempt.id).label('count')
        ).filter(
            LoginAttempt.timestamp >= cutoff
        ).group_by('interval').order_by('interval').all()
        
        # Get API requests
        api_requests = db.session.query(
            func.strftime('%Y-%m-%d %H:%M', APIRequest.timestamp).label('interval'),
            func.count(APIRequest.id).label('count')
        ).filter(
            APIRequest.timestamp >= cutoff
        ).group_by('interval').order_by('interval').all()
        
        return {
            'login_attempts': login_attempts,
            'api_requests': api_requests
        }
    except Exception as e:
        logger.error(f"Error getting security metrics: {str(e)}")
        return {
            'login_attempts': [],
            'api_requests': []
        } 