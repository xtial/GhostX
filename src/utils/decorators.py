from functools import wraps
from flask import redirect, url_for, request
from flask_login import current_user

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
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function 