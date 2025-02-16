from datetime import datetime, timedelta
import logging
from typing import Optional
from collections import defaultdict
from ..config import MAX_EMAILS_PER_HOUR, MAX_EMAILS_PER_DAY
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.database import db
from src.models.user import User, UserRole

logger = logging.getLogger(__name__)

# Create the limiter instance at module level
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

class RateLimiter:
    # Default rate limits per role
    RATE_LIMITS = {
        UserRole.USER.value: {
            'hourly': 10,
            'daily': 50
        },
        UserRole.PREMIUM.value: {
            'hourly': 50,
            'daily': 500
        },
        UserRole.ADMIN.value: {
            'hourly': 100,
            'daily': 1000
        }
    }
    
    @staticmethod
    def get_user_limits(user: User) -> dict:
        """Get rate limits for a user based on their role"""
        return RateLimiter.RATE_LIMITS.get(user.role, RateLimiter.RATE_LIMITS[UserRole.USER.value])
    
    @staticmethod
    def check_rate_limit(user_id: int) -> bool:
        """Check if a user has exceeded their rate limits"""
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            now = datetime.utcnow()
            limits = RateLimiter.get_user_limits(user)
            
            # Reset counters if needed
            if user.hourly_reset_time and user.hourly_reset_time <= now:
                user.hourly_email_count = 0
                user.hourly_reset_time = now + timedelta(hours=1)
            
            if user.daily_reset_time and user.daily_reset_time <= now:
                user.daily_email_count = 0
                user.daily_reset_time = now + timedelta(days=1)
            
            # Initialize reset times if not set
            if not user.hourly_reset_time:
                user.hourly_reset_time = now + timedelta(hours=1)
            if not user.daily_reset_time:
                user.daily_reset_time = now + timedelta(days=1)
            
            # Check limits
            if user.hourly_email_count >= limits['hourly']:
                logger.warning(f"User {user_id} exceeded hourly limit")
                return False
            
            if user.daily_email_count >= limits['daily']:
                logger.warning(f"User {user_id} exceeded daily limit")
                return False
            
            # Increment counters
            user.hourly_email_count += 1
            user.daily_email_count += 1
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return False
    
    @staticmethod
    def get_remaining_quota(user_id: int) -> Optional[dict]:
        """Get remaining email quota for a user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return None
            
            limits = RateLimiter.get_user_limits(user)
            
            return {
                'hourly': {
                    'limit': limits['hourly'],
                    'used': user.hourly_email_count,
                    'remaining': max(0, limits['hourly'] - user.hourly_email_count),
                    'reset_time': user.hourly_reset_time
                },
                'daily': {
                    'limit': limits['daily'],
                    'used': user.daily_email_count,
                    'remaining': max(0, limits['daily'] - user.daily_email_count),
                    'reset_time': user.daily_reset_time
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting quota: {str(e)}")
            return None
    
    @staticmethod
    def update_limits(role: str, hourly: int, daily: int) -> bool:
        """Update rate limits for a role"""
        try:
            if role not in RateLimiter.RATE_LIMITS:
                return False
            
            if hourly <= 0 or daily <= 0 or hourly > daily:
                return False
            
            RateLimiter.RATE_LIMITS[role] = {
                'hourly': hourly,
                'daily': daily
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating limits: {str(e)}")
            return False

# Helper function for external use
def check_rate_limit(user_id: int) -> bool:
    """Convenience function to check rate limit for a user"""
    return RateLimiter.check_rate_limit(user_id)

def check_rate_limit_old(user_id: int) -> bool:
    """
    Check if a user has exceeded their rate limits
    Returns True if within limits, False if exceeded
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return False
            
        now = datetime.utcnow()
        
        # Check if we need to reset counters
        if user.last_hourly_reset_time and (now - user.last_hourly_reset_time) > timedelta(hours=1):
            user.email_count = 0
            user.last_hourly_reset_time = now
            
        if user.last_daily_reset_time and (now - user.last_daily_reset_time) > timedelta(days=1):
            user.daily_email_count = 0
            user.last_daily_reset_time = now
            
        # Get limits based on user role
        hourly_limit = 10  # Default
        daily_limit = 50   # Default
        
        if user.role == 'premium':
            hourly_limit = 50
            daily_limit = 200
        elif user.role == 'admin':
            hourly_limit = 100
            daily_limit = 500
            
        # Check if within limits
        if user.email_count >= hourly_limit:
            return False
            
        if user.daily_email_count >= daily_limit:
            return False
            
        # Increment counters
        user.email_count += 1
        user.daily_email_count += 1
        
        db.session.commit()
        return True
        
    except Exception as e:
        # Log error
        return False 