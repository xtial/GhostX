from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, current_app, make_response
from flask_wtf.csrf import generate_csrf, CSRFProtect, CSRFError
from flask_login import login_required, current_user, login_user, logout_user
from src.models import db, User
from src.utils import is_password_strong, sanitize_input, validate_username
from src.utils.rate_limiter import limiter
from datetime import datetime
from functools import wraps
import logging

logger = logging.getLogger(__name__)
auth = Blueprint('auth', __name__)

@auth.after_request
def after_request(response):
    # Ensure CSRF token is available for AJAX requests
    if 'text/html' in response.headers.get('Content-Type', ''):
        response.set_cookie('csrf_token', generate_csrf())
    return response

@auth.errorhandler(CSRFError)
def handle_csrf_error(e):
    logger.error(f"CSRF error: {str(e)}")
    return jsonify({
        'success': False,
        'message': 'CSRF token validation failed'
    }), 400

@auth.before_request
def before_request():
    # Check if the route requires authentication
    if getattr(current_app.view_functions.get(request.endpoint), 'login_required', False):
        if not current_user.is_authenticated:
            # If AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': 'Session expired. Please log in again.',
                    'redirect': url_for('auth.login_page')
                }), 401
            # If regular request
            return redirect(url_for('auth.login_page'))
    
    # CSRF token check for POST requests
    if request.method == 'POST':
        if request.is_json:
            csrf_token = request.headers.get('X-CSRF-Token')
            if not csrf_token:
                logger.error("Missing CSRF token in headers")
                return jsonify({
                    'success': False,
                    'message': 'Missing CSRF token'
                }), 400
        else:
            csrf_token = request.form.get('csrf_token')
            if not csrf_token:
                logger.error("Missing CSRF token in form")
                return jsonify({
                    'success': False,
                    'message': 'Missing CSRF token'
                }), 400

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login_page', next=request.url))
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@auth.route('/login')
def login_page():
    try:
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('main.dashboard'))
        
        token = generate_csrf()
        response = make_response(render_template('login.html', csrf_token=token))
        response.set_cookie('csrf_token', token)
        return response
    except Exception as e:
        logger.error(f"Error in login page: {str(e)}")
        return render_template('login.html', csrf_token=generate_csrf(), error="An error occurred. Please try again.")

@auth.route('/register')
def register_page():
    try:
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('main.dashboard'))
        
        token = generate_csrf()
        return render_template('register.html', csrf_token=token)
    except Exception as e:
        logger.error(f"Error in register page: {str(e)}")
        return render_template('register.html', csrf_token=generate_csrf(), error="An error occurred. Please try again.")

@auth.route('/api/register', methods=['POST'])
@limiter.limit("5/hour")
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        username = sanitize_input(data.get('username', ''))
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')

        # Validate username
        if not username or not validate_username(username):
            return jsonify({
                'success': False, 
                'message': 'Username must be 3-20 characters long and contain only letters, numbers, and underscores'
            }), 400

        # Check if username exists
        if User.query.filter(User.username.ilike(username)).first():
            return jsonify({
                'success': False, 
                'message': 'Username already exists'
            }), 409

        # Validate password
        if not password or not confirm_password:
            return jsonify({
                'success': False,
                'message': 'Password is required'
            }), 400

        if password != confirm_password:
            return jsonify({
                'success': False, 
                'message': 'Passwords do not match'
            }), 400

        if not is_password_strong(password):
            return jsonify({
                'success': False, 
                'message': 'Password must be at least 8 characters and contain uppercase, lowercase, numbers, and special characters'
            }), 400

        # Create new user
        user = User(
            username=username,
            join_date=datetime.utcnow(),
            registration_ip=request.remote_addr,
            last_login_ip=request.remote_addr,
            last_login_date=datetime.utcnow()
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()

        # Log in the new user
        login_user(user, remember=True)
        
        logger.info(f"New user registered: {username} from IP: {request.remote_addr}")
        
        return jsonify({
            'success': True,
            'redirect': url_for('main.dashboard')
        }), 201

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': 'Registration failed. Please try again.'
        }), 500

@auth.route('/api/login', methods=['POST'])
@limiter.limit("10/minute")
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        username = sanitize_input(data.get('username', ''))
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password are required'}), 400

        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Update last login info before login
            user.last_login_date = datetime.utcnow()
            user.last_login_ip = request.remote_addr
            db.session.commit()
            
            # Now login the user
            login_user(user, remember=True)
            
            # Direct to appropriate dashboard
            if user.is_admin:
                return jsonify({
                    'success': True,
                    'redirect': url_for('admin.dashboard')
                })
            return jsonify({
                'success': True,
                'redirect': url_for('main.dashboard')
            })
        
        return jsonify({
            'success': False,
            'message': 'Invalid username or password'
        }), 401

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during login'
        }), 500

@auth.route('/logout')
@login_required
def logout():
    try:
        # Get username before logout for logging
        username = current_user.username
        
        # Logout the user using Flask-Login
        logout_user()
        
        # Clear Flask session
        session.clear()
        
        # Create response with logout page
        response = make_response(render_template('logout.html'))
        
        # Clear all cookies that might be used for authentication
        response.delete_cookie('session')
        response.delete_cookie('remember_token')
        response.delete_cookie('user_id')
        
        # Set no-cache headers to prevent browser back button from showing protected pages
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        # Log the logout
        logger.info(f"User logged out: {username}")
        
        return response
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return redirect(url_for('auth.login_page'))

@auth.route('/api/logout')
@login_required
def logout_api():
    try:
        # Get username before logout for logging
        username = current_user.username
        
        # Logout the user
        logout_user()
        
        # Clear session data
        session.clear()
        
        # Clear any session cookies
        response = jsonify({
            'success': True,
            'redirect': url_for('auth.login_page')
        })
        
        # Clear session cookie
        response.delete_cookie('session')
        
        # Log the logout
        logger.info(f"User logged out: {username}")
        
        return response
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Logout failed'
        }), 500

# Admin routes
@auth.route('/api/admin/stats')
@admin_required
def admin_stats():
    try:
        total_users = User.query.count()
        total_emails = User.query.with_entities(db.func.sum(User.email_count)).scalar() or 0
        banned_users = User.query.filter(User.is_active == False).count()
        
        return jsonify({
            'success': True,
            'total_users': total_users,
            'total_emails': total_emails,
            'banned_users': banned_users
        })
    except Exception as e:
        logger.error(f"Error getting admin stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get admin stats'
        }), 500

@auth.route('/api/admin/users')
@admin_required
def admin_users():
    try:
        users = User.query.all()
        return jsonify({
            'success': True,
            'users': [{
                'id': user.id,
                'username': user.username,
                'email_count': user.email_count,
                'join_date': user.join_date.isoformat(),
                'is_active': user.is_active,
                'last_login': user.last_login_date.isoformat() if user.last_login_date else None
            } for user in users]
        })
    except Exception as e:
        logger.error(f"Error getting users list: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get users list'
        }), 500

@auth.route('/api/admin/user/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status():
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({
            'success': False,
            'message': 'Invalid request data'
        }), 400

    try:
        user = User.query.filter(User.id == data['user_id']).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404

        user.is_active = data.get('active', not user.is_active)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f"User {'activated' if user.is_active else 'deactivated'} successfully"
        })
    except Exception as e:
        logger.error(f"Error toggling user status: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to update user status'
        }), 500

@auth.route('/api/admin/user/delete', methods=['POST'])
@admin_required
def delete_user():
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({
            'success': False,
            'message': 'Invalid request data'
        }), 400

    try:
        user = User.query.filter(User.id == data['user_id']).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404

        db.session.delete(user)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        })
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to delete user'
        }), 500

@auth.route('/api/admin/settings')
@admin_required
def get_settings():
    from src.config import MAX_EMAILS_PER_HOUR, MAX_EMAILS_PER_DAY
    return jsonify({
        'success': True,
        'max_emails_per_hour': MAX_EMAILS_PER_HOUR,
        'max_emails_per_day': MAX_EMAILS_PER_DAY
    })

@auth.route('/api/admin/settings/update', methods=['POST'])
@admin_required
def update_settings():
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'message': 'Invalid request data'
        }), 400

    try:
        # Update the settings in config
        from src.config import update_email_limits
        update_email_limits(
            data.get('max_emails_per_hour'),
            data.get('max_emails_per_day')
        )
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully'
        })
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update settings'
        }), 500 