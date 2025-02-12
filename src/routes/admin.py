from flask import Blueprint, jsonify, request, render_template, redirect, url_for
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func
from ..models import db, User, EmailTemplate, Permission, PermissionType, UserRole
from ..config import Config
from ..utils.email import send_spoofed_email
import logging
import traceback

logger = logging.getLogger(__name__)
admin = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            logger.warning(f"Unauthenticated user attempted to access admin route: {request.path}")
            return redirect(url_for('auth.login_page'))
        if not current_user.is_admin:
            logger.warning(f"Non-admin user {current_user.username} attempted to access admin route: {request.path}")
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def handle_error(e: Exception, error_type: str) -> tuple:
    """
    Centralized error handler that logs full details but returns safe messages to users
    """
    # Log full error details for debugging
    logger.error(f"Error in {error_type}: {str(e)}")
    logger.error(f"Stack trace: {traceback.format_exc()}")
    
    # Return a generic message to the user
    error_messages = {
        'stats': 'Failed to retrieve statistics',
        'users': 'Failed to retrieve user information',
        'user_status': 'Failed to update user status',
        'user_delete': 'Failed to delete user',
        'settings': 'Failed to manage settings',
        'templates': 'Failed to manage templates',
        'email': 'Failed to process email operation',
        'roles': 'Failed to manage roles',
        'permissions': 'Failed to manage permissions'
    }
    
    return jsonify({
        'success': False,
        'message': error_messages.get(error_type, 'An unexpected error occurred')
    }), 500

@admin.route('/')
@login_required
@admin_required
def index():
    logger.debug(f"Admin {current_user.username} accessing admin index")
    return redirect(url_for('admin.dashboard'))

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    logger.debug(f"Admin {current_user.username} accessing admin dashboard")
    return render_template('admin.html', csrf_token=generate_csrf())

@admin.route('/stats')
@login_required
@admin_required
def get_stats():
    try:
        # Basic stats
        total_users = User.query.count()
        banned_users = User.query.filter_by(is_active=False).count()
        total_emails = db.session.query(func.sum(User.email_count)).scalar() or 0
        
        # Email stats for the last 7 days
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        email_stats = db.session.query(
            func.date(User.last_login_date).label('date'),
            func.sum(User.email_count).label('count')
        ).filter(
            User.last_login_date >= seven_days_ago
        ).group_by(
            func.date(User.last_login_date)
        ).all()
        
        # User registration stats for the last 7 days
        user_stats = db.session.query(
            func.date(User.join_date).label('date'),
            func.count(User.id).label('count')
        ).filter(
            User.join_date >= seven_days_ago
        ).group_by(
            func.date(User.join_date)
        ).all()
        
        # Format stats for charts
        dates = [(seven_days_ago + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]
        email_data = {date: 0 for date in dates}
        user_data = {date: 0 for date in dates}
        
        for date, count in email_stats:
            email_data[date.strftime('%Y-%m-%d')] = count
            
        for date, count in user_stats:
            user_data[date.strftime('%Y-%m-%d')] = count
        
        return jsonify({
            'success': True,
            'total_users': total_users,
            'banned_users': banned_users,
            'total_emails': total_emails,
            'email_stats': {
                'labels': list(email_data.keys()),
                'values': list(email_data.values())
            },
            'user_stats': {
                'labels': list(user_data.keys()),
                'values': list(user_data.values())
            }
        })
    except Exception as e:
        return handle_error(e, 'stats')

@admin.route('/users')
@login_required
@admin_required
def get_users():
    try:
        users = User.query.all()
        return jsonify({
            'success': True,
            'users': [{
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active,
                'email_count': user.email_count,
                'join_date': user.join_date.isoformat(),
                'permissions': [p.name for p in user.permissions]
            } for user in users]
        })
    except Exception as e:
        return handle_error(e, 'users')

@admin.route('/user/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        active = data.get('active')
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID is required'
            }), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
            
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'message': 'Cannot modify your own account status'
            }), 403
            
        user.is_active = active
        db.session.commit()
        
        action = 'unbanned' if active else 'banned'
        logger.info(f"Admin {current_user.username} {action} user {user.username}")
        
        return jsonify({
            'success': True,
            'message': f'User {action} successfully'
        })
    except Exception as e:
        db.session.rollback()
        return handle_error(e, 'user_status')

@admin.route('/user/delete', methods=['POST'])
@login_required
@admin_required
def delete_user():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID is required'
            }), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
            
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'message': 'Cannot delete your own account'
            }), 403
            
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        logger.info(f"Admin {current_user.username} deleted user {username}")
        
        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return handle_error(e, 'user_delete')

@admin.route('/settings')
@login_required
@admin_required
def get_settings():
    try:
        return jsonify({
            'success': True,
            'max_emails_per_hour': Config.MAX_EMAILS_PER_HOUR,
            'max_emails_per_day': Config.MAX_EMAILS_PER_DAY
        })
    except Exception as e:
        return handle_error(e, 'settings')

@admin.route('/settings/update', methods=['POST'])
@login_required
@admin_required
def update_settings():
    try:
        data = request.get_json()
        max_emails_per_hour = data.get('max_emails_per_hour')
        max_emails_per_day = data.get('max_emails_per_day')
        
        if max_emails_per_hour is None or max_emails_per_day is None:
            return jsonify({
                'success': False,
                'message': 'Both max_emails_per_hour and max_emails_per_day are required'
            }), 400
            
        if not isinstance(max_emails_per_hour, int) or not isinstance(max_emails_per_day, int):
            return jsonify({
                'success': False,
                'message': 'Settings must be integer values'
            }), 400
            
        if max_emails_per_hour < 1 or max_emails_per_day < 1:
            return jsonify({
                'success': False,
                'message': 'Settings must be positive values'
            }), 400
            
        if max_emails_per_hour > max_emails_per_day:
            return jsonify({
                'success': False,
                'message': 'Hourly limit cannot be greater than daily limit'
            }), 400
        
        # Update configuration
        Config.MAX_EMAILS_PER_HOUR = max_emails_per_hour
        Config.MAX_EMAILS_PER_DAY = max_emails_per_day
        
        logger.info(f"Admin {current_user.username} updated email limits: {max_emails_per_hour}/hour, {max_emails_per_day}/day")
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully'
        })
    except Exception as e:
        return handle_error(e, 'settings')

@admin.route('/templates')
@login_required
@admin_required
def get_templates():
    try:
        templates = EmailTemplate.query.all()
        return jsonify({
            'success': True,
            'templates': [{
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'sender_name': template.sender_name,
                'sender_email': template.sender_email,
                'subject': template.subject,
                'html_content': template.html_content
            } for template in templates]
        })
    except Exception as e:
        return handle_error(e, 'templates')

@admin.route('/templates/<int:template_id>')
@login_required
@admin_required
def get_template(template_id):
    try:
        template = EmailTemplate.query.get(template_id)
        if not template:
            return jsonify({
                'success': False,
                'message': 'Template not found'
            }), 404
            
        return jsonify({
            'success': True,
            'template': {
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'sender_name': template.sender_name,
                'sender_email': template.sender_email,
                'subject': template.subject,
                'html_content': template.html_content
            }
        })
    except Exception as e:
        return handle_error(e, 'templates')

@admin.route('/send-email', methods=['POST'])
@login_required
@admin_required
def send_email():
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['recipient_email', 'sender_name', 'sender_email', 'subject', 'html_content']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field.replace("_", " ").title()} is required'
                }), 400
        
        # Send email
        success = send_spoofed_email(
            to_email=data['recipient_email'],
            from_name=data['sender_name'],
            from_email=data['sender_email'],
            subject=data['subject'],
            html_content=data['html_content']
        )
        
        if success:
            # Update email count for admin
            current_user.email_count += 1
            db.session.commit()
            
            logger.info(f"Admin {current_user.username} sent email to {data['recipient_email']}")
            
            return jsonify({
                'success': True,
                'message': 'Email sent successfully'
            })
        else:
            raise Exception('Failed to send email')
            
    except Exception as e:
        return handle_error(e, 'email')

@admin.route('/api/roles', methods=['GET'])
@login_required
@admin_required
def get_roles():
    try:
        # Get all available roles from the UserRole enum
        roles = [{
            'name': role.value,
            'description': role.name.replace('_', ' ').title(),
            'permissions': [],
            'user_count': User.query.filter_by(role=role.value).count(),
            'is_admin_role': role.value in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value],
            'is_default': role.value == UserRole.USER.value,
            'can_be_modified': role.value not in [UserRole.SUPER_ADMIN.value]  # Protect super admin role
        } for role in UserRole]
        
        # Get permissions for each role
        for role_data in roles:
            # Get a sample user with this role to get permissions
            user = User.query.filter_by(role=role_data['name']).first()
            if user:
                role_data['permissions'] = [{
                    'name': p.name,
                    'description': p.name.replace('_', ' ').title(),
                    'enabled': True
                } for p in user.permissions]
            
            # Add all available permissions that aren't enabled
            all_perms = set(perm.value for perm in PermissionType)
            enabled_perms = set(p['name'] for p in role_data['permissions'])
            disabled_perms = all_perms - enabled_perms
            
            role_data['permissions'].extend([{
                'name': perm,
                'description': perm.replace('_', ' ').title(),
                'enabled': False
            } for perm in disabled_perms])
            
            # Sort permissions by name
            role_data['permissions'].sort(key=lambda x: x['name'])
        
        return jsonify({
            'success': True,
            'roles': roles
        })
    except Exception as e:
        return handle_error(e, 'roles')

@admin.route('/api/permissions')
@login_required
@admin_required
def get_permissions():
    try:
        # Get all available permissions with metadata
        permissions = [{
            'name': perm.value,
            'description': perm.name.replace('_', ' ').title(),
            'category': perm.category,
            'is_admin_only': perm in PermissionType.admin_permissions(),
            'required_roles': [r.value for r in UserRole if perm in PermissionType.default_permissions(r)],
            'can_be_modified': True,  # Can be customized based on business rules
            'dependencies': [p.value for p in perm.dependencies],
            'conflicts_with': [p.value for p in perm.conflicts_with]
        } for perm in PermissionType]
        
        # Group permissions by category
        categories = {}
        for perm in permissions:
            category = perm['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(perm)
        
        return jsonify({
            'success': True,
            'permissions': permissions,
            'categories': categories
        })
    except Exception as e:
        return handle_error(e, 'permissions')

@admin.route('/api/user/role', methods=['POST'])
@login_required
@admin_required
def update_user_role():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        user_id = data.get('user_id')
        new_role = data.get('role')
        
        if not user_id or not new_role:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
            
        if new_role not in [role.value for role in UserRole]:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400
            
        # Store old role for logging
        old_role = user.role
        
        # Update user role
        user.role = new_role
        
        # Update is_admin flag based on role
        user.is_admin = new_role in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]
        
        # Commit changes
        db.session.commit()
        
        # Log the change
        logger.info(f"Admin {current_user.username} updated user {user.username} role from {old_role} to {new_role}")
        
        return jsonify({
            'success': True,
            'message': f'User role updated to {new_role}',
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'is_admin': user.is_admin
            }
        })
    except Exception as e:
        return handle_error(e, 'roles')

@admin.route('/api/user/permission', methods=['POST'])
@login_required
@admin_required
def toggle_user_permission():
    try:
        data = request.get_json()
        if not data or 'user_id' not in data or 'permission' not in data or 'enabled' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400

        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404

        try:
            permission_type = PermissionType(data['permission'])
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid permission type'
            }), 400

        # Don't allow modifying SUPER_ADMIN permissions
        if user.role == UserRole.SUPER_ADMIN.value:
            return jsonify({
                'success': False,
                'message': 'Cannot modify SUPER_ADMIN permissions'
            }), 403

        # Store old permission state for logging
        had_permission = user.has_permission(permission_type)

        if data['enabled']:
            success = user.add_permission(permission_type)
        else:
            success = user.remove_permission(permission_type)

        if success:
            # Commit changes to database
            db.session.commit()
            
            # Log the change
            logger.info(
                f"Admin {current_user.username} {'added' if data['enabled'] else 'removed'} "
                f"permission {permission_type.value} for user {user.username}"
            )
            
            return jsonify({
                'success': True,
                'message': f"Permission {'added' if data['enabled'] else 'removed'} successfully"
            })
        else:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Failed to update permission'
            }), 500

    except Exception as e:
        logger.error(f"Error in toggle_user_permission: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin.route('/api/admin/role/permissions', methods=['POST'])
@login_required
@admin_required
def update_role_permissions():
    try:
        data = request.get_json()
        role = data.get('role')
        permissions = data.get('permissions', [])
        
        if not role:
            return jsonify({'success': False, 'message': 'Missing role'}), 400
            
        if role not in [r.value for r in UserRole]:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400
            
        # Update permissions for all users with this role
        users = User.query.filter_by(role=role).all()
        for user in users:
            # Remove all existing permissions
            user.permissions = []
            
            # Add new permissions
            for perm in permissions:
                try:
                    permission_type = PermissionType(perm)
                    user.add_permission(permission_type)
                except ValueError:
                    continue
                    
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Updated permissions for {role} role'
        })
    except Exception as e:
        return handle_error(e, 'roles')

@admin.route('/api/role/<role>/permissions', methods=['GET'])
@login_required
@admin_required
def get_role_permissions(role):
    try:
        if role not in [r.value for r in UserRole]:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400
            
        # Get a sample user with this role to get permissions
        user = User.query.filter_by(role=role).first()
        enabled_permissions = set()
        
        if user:
            enabled_permissions = {p.name for p in user.permissions}
        else:
            # If no user exists with this role, use default permissions
            role_enum = UserRole(role)
            enabled_permissions = {p.value for p in PermissionType.default_permissions(role_enum)}
        
        # Get all available permissions
        permissions = [{
            'name': perm.value,
            'description': perm.name.replace('_', ' ').title(),
            'enabled': perm.value in enabled_permissions,
            'category': perm.category,
            'required_roles': [r.value for r in UserRole if perm in PermissionType.default_permissions(r)],
            'is_admin_only': perm in PermissionType.admin_permissions(),
            'can_be_modified': True,  # Can be customized based on business rules
            'dependencies': [p.value for p in perm.dependencies],
            'conflicts_with': [p.value for p in perm.conflicts_with]
        } for perm in PermissionType]
        
        return jsonify({
            'success': True,
            'role': role,
            'permissions': permissions,
            'is_admin_role': role in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value],
            'can_be_modified': role != UserRole.SUPER_ADMIN.value
        })
    except Exception as e:
        return handle_error(e, 'roles')

@admin.route('/api/role/permission', methods=['POST'])
@login_required
@admin_required
def update_role_permission():
    try:
        data = request.get_json()
        if not data or 'role' not in data or 'permission' not in data or 'enabled' not in data:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        role = data['role']
        permission = data['permission']
        enabled = data['enabled']
        
        if role not in [r.value for r in UserRole]:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400
            
        try:
            perm_type = PermissionType(permission)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid permission'}), 400
            
        # Don't allow modifying SUPER_ADMIN permissions
        if role == UserRole.SUPER_ADMIN.value:
            return jsonify({'success': False, 'message': 'Cannot modify SUPER_ADMIN permissions'}), 403
            
        # Update permissions for all users with this role
        users = User.query.filter_by(role=role).all()
        updated_count = 0
        
        for user in users:
            if enabled and not user.has_permission(perm_type):
                user.add_permission(perm_type)
                updated_count += 1
            elif not enabled and user.has_permission(perm_type):
                user.remove_permission(perm_type)
                updated_count += 1
        
        db.session.commit()
        
        logger.info(
            f"Admin {current_user.username} {'added' if enabled else 'removed'} "
            f"permission {permission} for role {role}. {updated_count} users affected."
        )
        
        return jsonify({
            'success': True,
            'message': f'Permission {"added to" if enabled else "removed from"} {role} role',
            'updated_users': updated_count
        })
    except Exception as e:
        return handle_error(e, 'roles')

@admin.route('/api/admin/user/<int:user_id>/permissions', methods=['GET'])
@login_required
@admin_required
def get_user_permissions(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404

        # Get all available permissions
        all_permissions = [perm for perm in PermissionType]
        
        # Format permissions with enabled status
        permissions = [{
            'name': perm.value,
            'description': perm.name.replace('_', ' ').title(),
            'enabled': user.has_permission(perm),
            'category': perm.category if hasattr(perm, 'category') else 'General',
            'is_admin_only': perm in PermissionType.admin_permissions() if hasattr(PermissionType, 'admin_permissions') else False
        } for perm in all_permissions]

        return jsonify({
            'success': True,
            'permissions': permissions
        })
        
    except Exception as e:
        return handle_error(e, 'permissions') 