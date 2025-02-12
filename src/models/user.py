from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from src import db
from enum import Enum

class UserRole(Enum):
    USER = 'user'
    PREMIUM = 'premium'
    ADMIN = 'admin'
    SUPER_ADMIN = 'super_admin'

class PermissionType(Enum):
    SEND_EMAIL = 'send_email'
    BULK_SEND = 'bulk_send'
    CREATE_TEMPLATE = 'create_template'
    EDIT_TEMPLATE = 'edit_template'
    VIEW_ANALYTICS = 'view_analytics'
    MANAGE_USERS = 'manage_users'
    SYSTEM_CONFIG = 'system_config'

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
    email = db.Column(db.String(120), unique=True)
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
    
    # Campaign and Template Stats
    total_campaigns = db.Column(db.Integer, default=0)
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
                                lazy='subquery',
                                backref=db.backref('users', lazy=True))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_permission(self, permission_type: PermissionType):
        if self.role == UserRole.SUPER_ADMIN.value:
            return True
        return str(permission_type.value) in [p.name for p in self.permissions]

    def add_permission(self, permission_type: PermissionType):
        if not self.has_permission(permission_type):
            permission = Permission.query.filter_by(name=permission_type.value).first()
            if not permission:
                permission = Permission(name=permission_type.value)
                db.session.add(permission)
            self.permissions.append(permission)
            db.session.commit()

    def remove_permission(self, permission_type: PermissionType):
        if self.has_permission(permission_type):
            permission = Permission.query.filter_by(name=permission_type.value).first()
            if permission:
                self.permissions.remove(permission)
                db.session.commit()

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
            'total_campaigns': self.total_campaigns,
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