from functools import wraps
from flask import redirect, url_for, request, flash, jsonify, g
from flask_login import current_user
from src.utils.rate_limiter import RateLimiter, check_rate_limit, release_concurrent_limit
import logging
from werkzeug.exceptions import Forbidden

logger = logging.getLogger(__name__)

def admin_required(f):
    """
    Decorator to ensure that a route can only be accessed by admin users.
    Must be used after the @login_required decorator.
    
    Example usage:
    @app.route('/admin')
    @login_required
    @admin_required
    def admin_page():
        return 'Admin only!'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            raise Forbidden("Admin access required")
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    """
    Decorator to ensure that a route can only be accessed by normal users.
    Must be used after the @login_required decorator.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login_page'))
        
        if current_user.is_admin:
            flash('Please use the admin dashboard.', 'info')
            return redirect(url_for('admin.index'))
            
        return f(*args, **kwargs)
    return decorated_function

def enforce_rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user or not current_user.is_authenticated:
            return f(*args, **kwargs)
            
        # Check if the endpoint is exempt from rate limiting
        if hasattr(f, '_rate_limit_exempt'):
            return f(*args, **kwargs)

        if not check_rate_limit(current_user.id):
            logger.warning(f"Rate limit exceeded for user {current_user.id}")
            return jsonify({
                'success': False,
                'message': 'Rate limit exceeded. Please try again later.'
            }), 429

        try:
            return f(*args, **kwargs)
        finally:
            release_concurrent_limit(current_user.id)
    return decorated_function

def track_api_usage(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user or not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': 'Authentication required'
            }), 401

        try:
            # Track API request before execution
            from src.models import APIRequest, db
            api_request = APIRequest(
                user_id=current_user.id,
                endpoint=request.endpoint,
                method=request.method,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(api_request)
            db.session.commit()

            # Execute the function
            result = f(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error in API tracking: {str(e)}")
            raise

    return decorated_function

def rate_limit_exempt(f):
    """Mark a route as exempt from rate limiting"""
    f._rate_limit_exempt = True
    return f 