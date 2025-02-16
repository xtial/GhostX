from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, current_app, make_response, flash
from flask_wtf.csrf import generate_csrf, CSRFProtect, CSRFError
from flask_login import login_required, current_user, login_user, logout_user
from src.models import db, User
from src.models.registration_attempt import RegistrationAttempt
from src.utils import is_password_strong, sanitize_input, validate_username
from src.utils.rate_limiter import limiter
from datetime import datetime
from functools import wraps
import logging
import hashlib

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
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login_page', next=request.url))
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login_page', next=request.url))
        if current_user.is_admin:
            flash('Please use the admin dashboard.', 'info')
            return redirect(url_for('admin.dashboard'))
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

def generate_browser_fingerprint():
    """Generate a simple browser fingerprint from request headers"""
    user_agent = request.headers.get('User-Agent', '')
    accept_lang = request.headers.get('Accept-Language', '')
    platform = request.headers.get('Sec-Ch-Ua-Platform', '')
    
    # Create a unique fingerprint from available data
    fingerprint_data = f"{user_agent}|{accept_lang}|{platform}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()

@auth.route('/api/register', methods=['POST'])
@limiter.limit("5/hour")
def register():
    """Register a new user account"""
    try:
        data = request.get_json()
        
        # Get client information
        ip_address = request.remote_addr
        browser_fingerprint = generate_browser_fingerprint()
        user_agent = request.headers.get('User-Agent', '')

        # Check registration limits
        allowed, reason = RegistrationAttempt.check_limits(ip_address, browser_fingerprint)
        if not allowed:
            # Record failed attempt
            RegistrationAttempt.record_attempt(
                ip_address=ip_address,
                browser_fingerprint=browser_fingerprint,
                user_agent=user_agent,
                username=data.get('username'),
                success=False
            )
            return jsonify({
                'success': False,
                'message': reason
            }), 429

        # Validate required fields
        required_fields = ['username', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field.title()} is required'
                }), 400

        username = sanitize_input(data['username'])
        password = data['password']
        email = sanitize_input(data.get('email', ''))  # Optional email

        # Validate username
        if not validate_username(username):
            return jsonify({
                'success': False,
                'message': 'Invalid username format'
            }), 400

        # Check if username exists
        if User.query.filter_by(username=username).first():
            return jsonify({
                'success': False,
                'message': 'Username already exists'
            }), 400

        # Check if email exists (only if provided)
        if email and User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'message': 'Email already registered'
            }), 400

        # Validate password strength
        if not is_password_strong(password):
            return jsonify({
                'success': False,
                'message': 'Password is not strong enough'
            }), 400

        # Create new user
        user = User(
            username=username,
            email=email if email else None
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()

        # Record successful registration
        RegistrationAttempt.record_attempt(
            ip_address=ip_address,
            browser_fingerprint=browser_fingerprint,
            user_agent=user_agent,
            username=username,
            email=email if email else None,
            success=True
        )

        # Log in the new user
        login_user(user)

        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'redirect': url_for('main.dashboard')
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in registration: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Registration failed. Please try again later.'
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

@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Handle regular logout requests with page redirect"""
    try:
        # Store info before logout
        was_admin = current_user.is_admin
        username = current_user.username
        
        # Update last activity
        current_user.last_login_date = datetime.utcnow()
        db.session.commit()
        
        # Perform logout
        logout_user()
        
        # Clear all session data
        session.clear()
        
        # Create response with logout page
        response = make_response(render_template('logout.html'))
        
        # Clear all authentication-related cookies
        cookies_to_clear = [
            'session',
            'remember_token',
            'user_id',
            '_fresh',
            '_id',
            'csrf_token'
        ]
        
        for cookie in cookies_to_clear:
            response.delete_cookie(cookie, path='/', domain=None)
        
        # Set security headers
        response.headers.update({
            'Cache-Control': 'no-cache, no-store, must-revalidate, private',
            'Pragma': 'no-cache',
            'Expires': '0',
            'X-Frame-Options': 'DENY',
            'X-Content-Type-Options': 'nosniff',
            'Clear-Site-Data': '"cache", "cookies", "storage"'
        })
        
        # Log the logout
        logger.info(f"User logged out successfully: {username} (Admin: {was_admin})")
        
        return response
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        # Even if there's an error, try to clear the session
        session.clear()
        return redirect(url_for('auth.login_page'))

@auth.route('/api/logout', methods=['POST'])
@login_required
def logout_api():
    """Handle API logout requests with JSON response"""
    try:
        # Store info before logout
        was_admin = current_user.is_admin
        username = current_user.username
        
        # Update last activity
        current_user.last_login_date = datetime.utcnow()
        db.session.commit()
        
        # Perform logout
        logout_user()
        
        # Clear all session data
        session.clear()
        
        # Prepare response
        response = jsonify({
            'success': True,
            'message': 'Logged out successfully',
            'redirect': url_for('auth.login_page')
        })
        
        # Clear all authentication-related cookies
        cookies_to_clear = [
            'session',
            'remember_token',
            'user_id',
            '_fresh',
            '_id',
            'csrf_token'
        ]
        
        for cookie in cookies_to_clear:
            response.delete_cookie(cookie, path='/', domain=None)
        
        # Set security headers
        response.headers.update({
            'Cache-Control': 'no-cache, no-store, must-revalidate, private',
            'Pragma': 'no-cache',
            'Expires': '0',
            'X-Frame-Options': 'DENY',
            'X-Content-Type-Options': 'nosniff',
            'Clear-Site-Data': '"cache", "cookies", "storage"'
        })
        
        # Log the logout
        logger.info(f"API logout successful: {username} (Admin: {was_admin})")
        
        return response
        
    except Exception as e:
        logger.error(f"Error during API logout: {str(e)}")
        # Even if there's an error, try to clear the session
        session.clear()
        return jsonify({
            'success': False,
            'message': 'Logout failed, but session was cleared',
            'redirect': url_for('auth.login_page')
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