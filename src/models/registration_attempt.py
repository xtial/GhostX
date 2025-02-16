from datetime import datetime, timedelta
from src.database import db
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

class RegistrationAttempt(db.Model):
    """Model to track registration attempts for rate limiting"""
    __tablename__ = 'registration_attempts'

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)  # IPv6 support
    browser_fingerprint = db.Column(db.String(64), nullable=False, index=True)
    user_agent = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(64), nullable=True)
    email = db.Column(db.String(120), nullable=True)

    @classmethod
    def reset_limits(cls) -> tuple[bool, str]:
        """
        Reset all rate limits by clearing the registration attempts table
        Returns: (success: bool, message: str)
        """
        try:
            # Delete all records from the table
            cls.query.delete()
            db.session.commit()
            logger.info("Successfully reset all registration rate limits")
            return True, "Rate limits reset successfully"
        except Exception as e:
            db.session.rollback()
            error_msg = f"Failed to reset rate limits: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    @classmethod
    def check_limits(cls, ip_address: str, browser_fingerprint: str) -> tuple[bool, str]:
        """
        Check if registration should be allowed based on various limits
        Returns: (allowed: bool, reason: str)
        """
        try:
            # Time windows for checks
            hour_ago = datetime.utcnow() - timedelta(hours=1)
            day_ago = datetime.utcnow() - timedelta(days=1)
            month_ago = datetime.utcnow() - timedelta(days=30)

            # Check hourly limit per IP (3 attempts)
            hourly_ip_count = cls.query.filter(
                cls.ip_address == ip_address,
                cls.timestamp >= hour_ago
            ).count()
            if hourly_ip_count >= 3:
                return False, "Too many registration attempts from this IP. Please try again later."

            # Check daily limit per IP (5 attempts)
            daily_ip_count = cls.query.filter(
                cls.ip_address == ip_address,
                cls.timestamp >= day_ago
            ).count()
            if daily_ip_count >= 5:
                return False, "Daily registration limit reached for this IP. Please try again tomorrow."

            # Check monthly limit per IP (10 successful registrations)
            monthly_success_ip_count = cls.query.filter(
                cls.ip_address == ip_address,
                cls.timestamp >= month_ago,
                cls.success == True
            ).count()
            if monthly_success_ip_count >= 10:
                return False, "Monthly account creation limit reached for this IP."

            # Check browser fingerprint limits (2 accounts per browser per day)
            daily_browser_count = cls.query.filter(
                cls.browser_fingerprint == browser_fingerprint,
                cls.timestamp >= day_ago,
                cls.success == True
            ).count()
            if daily_browser_count >= 2:
                return False, "Daily account limit reached for this browser."

            return True, ""

        except Exception as e:
            db.session.rollback()
            return False, "Error checking registration limits. Please try again later."

    @classmethod
    def record_attempt(cls, ip_address: str, browser_fingerprint: str, user_agent: str, 
                      username: str = None, email: str = None, success: bool = False):
        """Record a registration attempt"""
        try:
            attempt = cls(
                ip_address=ip_address,
                browser_fingerprint=browser_fingerprint,
                user_agent=user_agent,
                username=username,
                email=email,
                success=success
            )
            db.session.add(attempt)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise 