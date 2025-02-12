from functools import wraps
from flask import redirect, url_for, request, flash
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
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login_page'))
        
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.dashboard'))
            
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