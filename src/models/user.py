from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from src.database import db
from enum import Enum
from flask import current_app

class UserRole(Enum):
    USER = 'user'
    PREMIUM = 'premium'
    ADMIN = 'admin'
    SUPER_ADMIN = 'super_admin'

    @classmethod
    def get_default(cls):
        return cls.USER

    @classmethod
    def from_str(cls, role_str):
        try:
            return cls(role_str) if role_str else cls.get_default()
        except ValueError:
            return cls.get_default()

    def __str__(self):
        return self.value

class PermissionType(Enum):
    # Basic Permissions
    SEND_EMAIL = 'send_email'
    BULK_SEND = 'bulk_send'
    CREATE_TEMPLATE = 'create_template'
    EDIT_TEMPLATE = 'edit_template'
    VIEW_ANALYTICS = 'view_analytics'
    
    # Admin Permissions
    MANAGE_USERS = 'manage_users'
    SYSTEM_CONFIG = 'system_config'
    MANAGE_ROLES = 'manage_roles'
    VIEW_LOGS = 'view_logs'
    MANAGE_TEMPLATES = 'manage_templates'

    @property
    def category(self):
        admin_perms = {'MANAGE_USERS', 'SYSTEM_CONFIG', 'MANAGE_ROLES', 'VIEW_LOGS', 'MANAGE_TEMPLATES'}
        template_perms = {'CREATE_TEMPLATE', 'EDIT_TEMPLATE', 'MANAGE_TEMPLATES'}
        email_perms = {'SEND_EMAIL', 'BULK_SEND'}
        analytics_perms = {'VIEW_ANALYTICS', 'VIEW_LOGS'}
        
        if self.name in admin_perms:
            return 'Administration'
        elif self.name in template_perms:
            return 'Templates'
        elif self.name in email_perms:
            return 'Email'
        elif self.name in analytics_perms:
            return 'Analytics'
        return 'General'

    @property
    def dependencies(self):
        # Define permission dependencies
        deps = {
            PermissionType.BULK_SEND: {PermissionType.SEND_EMAIL},
            PermissionType.MANAGE_TEMPLATES: {PermissionType.CREATE_TEMPLATE, PermissionType.EDIT_TEMPLATE},
            PermissionType.SYSTEM_CONFIG: {PermissionType.VIEW_LOGS},
            PermissionType.MANAGE_ROLES: {PermissionType.MANAGE_USERS}
        }
        return deps.get(self, set())

    @property
    def conflicts_with(self):
        # Define conflicting permissions
        conflicts = {
            # Example: A regular user permission might conflict with admin permissions
            PermissionType.SEND_EMAIL: set()  # No conflicts for basic permissions
        }
        return conflicts.get(self, set())

    @classmethod
    def admin_permissions(cls):
        return {
            cls.MANAGE_USERS,
            cls.SYSTEM_CONFIG,
            cls.MANAGE_ROLES,
            cls.VIEW_LOGS,
            cls.MANAGE_TEMPLATES
        }

    @classmethod
    def default_permissions(cls, role: 'UserRole'):
        if role == UserRole.SUPER_ADMIN:
            return set(cls)
        elif role == UserRole.ADMIN:
            return {
                cls.SEND_EMAIL,
                cls.BULK_SEND,
                cls.CREATE_TEMPLATE,
                cls.EDIT_TEMPLATE,
                cls.VIEW_ANALYTICS,
                cls.MANAGE_USERS,
                cls.VIEW_LOGS,
                cls.MANAGE_TEMPLATES
            }
        elif role == UserRole.PREMIUM:
            return {
                cls.SEND_EMAIL,
                cls.BULK_SEND,
                cls.CREATE_TEMPLATE,
                cls.EDIT_TEMPLATE,
                cls.VIEW_ANALYTICS
            }
        else:  # Basic user
            return {
                cls.SEND_EMAIL,
                cls.CREATE_TEMPLATE
            }

# Permission model for storing available permissions
class Permission(db.Model):
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Association table for user permissions
user_permissions = db.Table('user_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE')),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE')),
    db.UniqueConstraint('user_id', 'permission_id', name='unique_user_permission')
)

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(20), default=UserRole.USER.value)
    
    # Email Usage Tracking
    email_count = db.Column(db.Integer, default=0)
    daily_email_count = db.Column(db.Integer, default=0)
    successful_emails = db.Column(db.Integer, default=0)
    failed_emails = db.Column(db.Integer, default=0)
    last_hourly_reset = db.Column(db.Integer, default=0)
    last_daily_reset = db.Column(db.Integer, default=0)
    last_hourly_reset_time = db.Column(db.DateTime)
    last_daily_reset_time = db.Column(db.DateTime)
    
    # Template Stats
    total_templates = db.Column(db.Integer, default=0)
    total_opens = db.Column(db.Integer, default=0)
    total_clicks = db.Column(db.Integer, default=0)
    
    # Account Information
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_date = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))
    registration_ip = db.Column(db.String(45))
    
    # Account Status and Settings
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    dashboard_layout = db.Column(db.JSON)
    email_notifications = db.Column(db.Boolean, default=True)
    
    # Security Features
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime)
    account_locked_until = db.Column(db.DateTime)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))
    
    # Permissions - Using the association table
    permissions = db.relationship('Permission', 
                                secondary=user_permissions,
                                lazy='dynamic',
                                cascade='all, delete')


    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # Ensure role is properly set
        self.role = UserRole.from_str(kwargs.get('role')).value
        if self.role == UserRole.SUPER_ADMIN.value:
            self.is_admin = True
        self._setup_default_permissions()

    def _setup_default_permissions(self):
        """Set up default permissions based on user role"""
        try:
            role = UserRole.from_str(self.role)
            default_perms = PermissionType.default_permissions(role)
            
            for perm in default_perms:
                permission = Permission.query.filter_by(name=perm.value).first()
                if not permission:
                    permission = Permission(name=perm.value, 
                                         description=perm.name.replace('_', ' ').title())
                    db.session.add(permission)
                if permission not in self.permissions:
                    self.permissions.append(permission)
        except Exception as e:
            current_app.logger.error(f"Error setting up default permissions: {str(e)}")
            # Set minimal permissions if there's an error
            role = UserRole.USER
            default_perms = {PermissionType.SEND_EMAIL}

    def has_permission(self, permission_type: PermissionType) -> bool:
        """Check if user has a specific permission"""
        if self.role == UserRole.SUPER_ADMIN.value:
            return True
            
        permission = Permission.query.filter_by(name=permission_type.value).first()
        if not permission:
            return False
            
        return permission in self.permissions

    def add_permission(self, permission_type: PermissionType) -> bool:
        """Add a permission to the user"""
        if self.has_permission(permission_type):
            return True
            
        permission = Permission.query.filter_by(name=permission_type.value).first()
        if not permission:
            permission = Permission(name=permission_type.value,
                                 description=permission_type.name.replace('_', ' ').title())
            db.session.add(permission)
            
        self.permissions.append(permission)
        return True

    def remove_permission(self, permission_type: PermissionType) -> bool:
        """Remove a permission from the user"""
        permission = Permission.query.filter_by(name=permission_type.value).first()
        if permission and permission in self.permissions:
            self.permissions.remove(permission)
            return True
        return False

    def get_permissions(self) -> list:
        """Get list of user's permissions"""
        return [PermissionType(p.name) for p in self.permissions]

    def update_role(self, new_role: str) -> bool:
        """Update user's role and adjust permissions accordingly"""
        try:
            role = UserRole(new_role)
            old_role = self.role
            self.role = role.value
            
            # Update admin status
            self.is_admin = role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
            
            # Clear existing permissions
            self.permissions = []
            
            # Set up new default permissions
            self._setup_default_permissions()
            
            return True
        except ValueError:
            return False

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_hourly_remaining(self):
        self.check_and_reset_limits()
        hourly_sent = self.email_count - self.last_hourly_reset
        return max(0, self.get_hourly_limit() - hourly_sent)

    def get_daily_remaining(self):
        self.check_and_reset_limits()
        daily_sent = self.email_count - self.last_daily_reset
        return max(0, self.get_daily_limit() - daily_sent)

    def get_hourly_limit(self):
        if self.role == UserRole.PREMIUM.value:
            return 50
        return 10

    def get_daily_limit(self):
        if self.role == UserRole.PREMIUM.value:
            return 200
        return 50

    def update_dashboard_layout(self, layout):
        self.dashboard_layout = layout
        db.session.commit()

    def get_stats(self):
        return {
            'total_emails': self.email_count,
            'successful_emails': self.successful_emails,
            'failed_emails': self.failed_emails,
            'success_rate': (self.successful_emails / self.email_count * 100) if self.email_count > 0 else 0,
            'total_templates': self.total_templates,
            'total_opens': self.total_opens,
            'total_clicks': self.total_clicks,
            'click_rate': (self.total_clicks / self.total_opens * 100) if self.total_opens > 0 else 0
        }

    def is_account_locked(self):
        if self.account_locked_until and self.account_locked_until > datetime.utcnow():
            return True
        return False

    def increment_failed_login(self):
        self.failed_login_attempts += 1
        self.last_failed_login = datetime.utcnow()
        
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.account_locked_until = datetime.utcnow() + timedelta(minutes=15)

    def reset_failed_login(self):
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.account_locked_until = None

    def check_and_reset_limits(self):
        """Check and reset hourly/daily limits if needed"""
        now = datetime.utcnow()
        
        # Check hourly reset
        if (not self.last_hourly_reset_time or 
            now - self.last_hourly_reset_time > timedelta(hours=1)):
            self.last_hourly_reset = self.email_count
            self.last_hourly_reset_time = now
        
        # Check daily reset
        if (not self.last_daily_reset_time or 
            now - self.last_daily_reset_time > timedelta(days=1)):
            self.last_daily_reset = self.email_count
            self.last_daily_reset_time = now 