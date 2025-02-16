from datetime import datetime, timedelta
import logging
from typing import Optional, Dict
from collections import defaultdict
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.database import db
from src.models.user import User, UserRole
from src.models.registration_attempt import RegistrationAttempt
import redis
from src.config import Config
from flask import jsonify, request
from flask_login import current_user

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self._redis = None
        self._local_storage = defaultdict(lambda: {
            'hourly': {'count': 0, 'reset_at': datetime.utcnow() + timedelta(hours=1)},
            'daily': {'count': 0, 'reset_at': datetime.utcnow() + timedelta(days=1)},
            'concurrent': 0
        })
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection for distributed rate limiting"""
        if Config.REDIS_CONFIG['host'] != 'localhost':
            try:
                self._redis = redis.Redis(
                    host=Config.REDIS_CONFIG['host'],
                    port=Config.REDIS_CONFIG['port'],
                    db=Config.REDIS_CONFIG['db'],
                    password=Config.REDIS_CONFIG['password'],
                    ssl=Config.REDIS_CONFIG['ssl'],
                    socket_timeout=Config.REDIS_CONFIG['socket_timeout'],
                    decode_responses=True
                )
                self._redis.ping()
                logger.info("Redis connection established for rate limiting")
            except Exception as e:
                logger.warning(f"Redis connection failed, using local storage: {str(e)}")
                self._redis = None

    def _get_redis_key(self, user_id: int, limit_type: str) -> str:
        """Generate Redis key for rate limiting"""
        return f"rate_limit:{user_id}:{limit_type}"

    def check_rate_limit(self, user_id: int) -> bool:
        """Check if a user has exceeded their rate limits"""
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False

            limits = Config.get_rate_limits(user.role)

            if self._redis:
                return self._check_redis_limits(user_id, limits)
            else:
                return self._check_local_limits(user_id, limits)

        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return False

    def _check_redis_limits(self, user_id: int, limits: dict) -> bool:
        """Check rate limits using Redis"""
        try:
            pipe = self._redis.pipeline()
            now = datetime.utcnow()

            # Check and update hourly limit
            hourly_key = self._get_redis_key(user_id, 'hourly')
            hourly_count = int(self._redis.get(hourly_key) or 0)
            if hourly_count >= limits['hourly']:
                return False
            pipe.incr(hourly_key)
            pipe.expire(hourly_key, 3600)  # 1 hour

            # Check and update daily limit
            daily_key = self._get_redis_key(user_id, 'daily')
            daily_count = int(self._redis.get(daily_key) or 0)
            if daily_count >= limits['daily']:
                return False
            pipe.incr(daily_key)
            pipe.expire(daily_key, 86400)  # 24 hours

            # Check and update concurrent limit
            concurrent_key = self._get_redis_key(user_id, 'concurrent')
            concurrent_count = int(self._redis.get(concurrent_key) or 0)
            if concurrent_count >= limits['concurrent']:
                return False
            pipe.incr(concurrent_key)
            pipe.expire(concurrent_key, 300)  # 5 minutes

            pipe.execute()
            return True

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {str(e)}")
            return self._check_local_limits(user_id, limits)

    def _check_local_limits(self, user_id: int, limits: dict) -> bool:
        """Check rate limits using local storage"""
        now = datetime.utcnow()
        user_limits = self._local_storage[user_id]

        # Reset expired counters
        if now >= user_limits['hourly']['reset_at']:
            user_limits['hourly'] = {
                'count': 0,
                'reset_at': now + timedelta(hours=1)
            }
        if now >= user_limits['daily']['reset_at']:
            user_limits['daily'] = {
                'count': 0,
                'reset_at': now + timedelta(days=1)
            }

        # Check limits
        if user_limits['hourly']['count'] >= limits['hourly']:
            return False
        if user_limits['daily']['count'] >= limits['daily']:
            return False
        if user_limits['concurrent'] >= limits['concurrent']:
            return False

        # Update counters
        user_limits['hourly']['count'] += 1
        user_limits['daily']['count'] += 1
        user_limits['concurrent'] += 1

        return True

    def release_concurrent_limit(self, user_id: int) -> None:
        """Release a concurrent email slot"""
        try:
            if self._redis:
                concurrent_key = self._get_redis_key(user_id, 'concurrent')
                self._redis.decr(concurrent_key)
            else:
                self._local_storage[user_id]['concurrent'] = max(
                    0, self._local_storage[user_id]['concurrent'] - 1
                )
        except Exception as e:
            logger.error(f"Error releasing concurrent limit: {str(e)}")

    def get_remaining_quota(self, user_id: int) -> Optional[dict]:
        """Get remaining email quota for a user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return None

            limits = Config.get_rate_limits(user.role)

            if self._redis:
                return self._get_redis_quota(user_id, limits)
            else:
                return self._get_local_quota(user_id, limits)

        except Exception as e:
            logger.error(f"Error getting quota: {str(e)}")
            return None

    def _get_redis_quota(self, user_id: int, limits: dict) -> dict:
        """Get quota information from Redis"""
        try:
            pipe = self._redis.pipeline()
            
            # Get all counters and TTLs
            hourly_key = self._get_redis_key(user_id, 'hourly')
            daily_key = self._get_redis_key(user_id, 'daily')
            concurrent_key = self._get_redis_key(user_id, 'concurrent')

            pipe.get(hourly_key)
            pipe.ttl(hourly_key)
            pipe.get(daily_key)
            pipe.ttl(daily_key)
            pipe.get(concurrent_key)

            results = pipe.execute()
            hourly_count = int(results[0] or 0)
            hourly_ttl = max(0, results[1])
            daily_count = int(results[2] or 0)
            daily_ttl = max(0, results[3])
            concurrent_count = int(results[4] or 0)

            return {
                'hourly': {
                    'limit': limits['hourly'],
                    'used': hourly_count,
                    'remaining': max(0, limits['hourly'] - hourly_count),
                    'reset_in': hourly_ttl
                },
                'daily': {
                    'limit': limits['daily'],
                    'used': daily_count,
                    'remaining': max(0, limits['daily'] - daily_count),
                    'reset_in': daily_ttl
                },
                'concurrent': {
                    'limit': limits['concurrent'],
                    'used': concurrent_count,
                    'remaining': max(0, limits['concurrent'] - concurrent_count)
                }
            }

        except Exception as e:
            logger.error(f"Error getting Redis quota: {str(e)}")
            return self._get_local_quota(user_id, limits)

    def _get_local_quota(self, user_id: int, limits: dict) -> dict:
        """Get quota information from local storage"""
        now = datetime.utcnow()
        user_limits = self._local_storage[user_id]

        return {
            'hourly': {
                'limit': limits['hourly'],
                'used': user_limits['hourly']['count'],
                'remaining': max(0, limits['hourly'] - user_limits['hourly']['count']),
                'reset_in': int((user_limits['hourly']['reset_at'] - now).total_seconds())
            },
            'daily': {
                'limit': limits['daily'],
                'used': user_limits['daily']['count'],
                'remaining': max(0, limits['daily'] - user_limits['daily']['count']),
                'reset_in': int((user_limits['daily']['reset_at'] - now).total_seconds())
            },
            'concurrent': {
                'limit': limits['concurrent'],
                'used': user_limits['concurrent'],
                'remaining': max(0, limits['concurrent'] - user_limits['concurrent'])
            }
        }

# Create global instance
rate_limiter = RateLimiter()

# Helper functions for external use
def check_rate_limit(user_id: int) -> bool:
    """Convenience function to check rate limit for a user"""
    return rate_limiter.check_rate_limit(user_id)

def release_concurrent_limit(user_id: int) -> None:
    """Convenience function to release concurrent limit"""
    rate_limiter.release_concurrent_limit(user_id)

def get_remaining_quota(user_id: int) -> Optional[dict]:
    """Convenience function to get remaining quota"""
    return rate_limiter.get_remaining_quota(user_id)

# Create limiter instance with dynamic limits
def get_user_limits():
    """Dynamic rate limit based on user role"""
    if not current_user.is_authenticated:
        return ["20 per hour", "100 per day"]
    
    if current_user.is_admin:
        return ["1000 per hour", "5000 per day"]
        
    return ["20 per hour", "100 per day"]

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=Config.REDIS_URL,
    strategy="fixed-window-elastic-expiry"  # More forgiving strategy for bursts
)

def init_limiter(app):
    """Initialize the limiter with the app"""
    limiter.init_app(app)
    
    # Register error handler for rate limit exceeded
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            'success': False,
            'message': 'Rate limit exceeded. Please try again later.',
            'retry_after': e.description
        }), 429
    
    # Apply default dynamic limits to all routes
    @app.before_request
    def check_rate_limit():
        if current_user.is_authenticated:
            endpoint = request.endpoint
            if endpoint and 'admin' in endpoint:
                # Skip rate limiting for admin endpoints
                return
            
            if current_user.is_admin:
                limiter.limits = ["1000 per hour", "5000 per day"]
            else:
                limiter.limits = ["20 per hour", "100 per day"]
    
    return limiter

# Export the limiter instance
__all__ = ['limiter', 'init_limiter', 'check_rate_limit', 'release_concurrent_limit', 'get_remaining_quota'] 