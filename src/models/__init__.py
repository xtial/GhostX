"""
Models package
"""

from flask_login import UserMixin
from src import db

from .user import User, UserRole, Permission, PermissionType
from .campaign import Campaign, CampaignStatus
from .tracking import EmailTracking, EventType
from .email_template import EmailTemplate
from .session import Session
from .security import LoginAttempt, APIRequest, SecurityLog

__all__ = [
    'User',
    'UserRole',
    'Permission',
    'PermissionType',
    'Campaign',
    'CampaignStatus',
    'EmailTracking',
    'EventType',
    'EmailTemplate',
    'Session',
    'LoginAttempt',
    'APIRequest',
    'SecurityLog'
] 