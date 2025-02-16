"""
Models package
"""

from flask_login import UserMixin
from src.database import db

from .user import User, UserRole, Permission, PermissionType
from .tracking import EmailTracking, EventType
from .email_template import EmailTemplate
from .session import Session
from .security import LoginAttempt, APIRequest, SecurityLog
from .registration_attempt import RegistrationAttempt

__all__ = [
    'User',
    'UserRole',
    'Permission',
    'PermissionType',
    'EmailTracking',
    'EventType',
    'EmailTemplate',
    'Session',
    'LoginAttempt',
    'APIRequest',
    'SecurityLog',
    'RegistrationAttempt'
] 