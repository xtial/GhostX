from datetime import datetime
import threading
import time
import logging
from typing import Dict, Optional
from src.database import db
from src.models import EmailTemplate, EmailTracking, User
from src.utils.email_sender import send_email
from src.utils.rate_limiter import check_rate_limit, release_concurrent_limit
from src.config import Config

logger = logging.getLogger(__name__)

class EmailWorker:
    def __init__(self):
        self.running = False
        self.worker_thread = None
        self.lock = threading.Lock()
        self.user_locks = {}  # Lock per user to prevent concurrent sending

    def _get_user_lock(self, user_id: int) -> threading.Lock:
        """Get or create a lock for a specific user"""
        with self.lock:
            if user_id not in self.user_locks:
                self.user_locks[user_id] = threading.Lock()
            return self.user_locks[user_id]

    def send_email(self, user_id: int, recipient: str, template: EmailTemplate) -> bool:
        """Send a single email with rate limiting"""
        user_lock = self._get_user_lock(user_id)
        
        try:
            with user_lock:  # Ensure only one email operation per user runs at a time
                if not check_rate_limit(user_id):
                    logger.warning(f"Rate limit reached for user {user_id}")
                    return False
                    
                # Create tracking entry
                tracking = EmailTracking(
                    user_id=user_id,
                    recipient_email=recipient,
                    template_id=template.id,
                    message_id=EmailTracking.generate_message_id(),
                    tracking_id=EmailTracking.generate_tracking_id()
                )
                db.session.add(tracking)
                db.session.commit()

                # Send email
                success = send_email(
                    recipient_email=recipient,
                    template=template,
                    tracking_id=tracking.tracking_id
                )

                # Update tracking and stats
                if success:
                    tracking.track_event('sent')
                    template.update_stats(success=True)
                else:
                    tracking.track_event('failed')
                    template.update_stats(success=False)

                db.session.commit()
                return success

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
        finally:
            release_concurrent_limit(user_id)

email_worker = EmailWorker() 