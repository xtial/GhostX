from datetime import datetime
from src.database import db
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class EventType(Enum):
    SENT = 'sent'
    DELIVERED = 'delivered'
    OPENED = 'opened'
    CLICKED = 'clicked'
    BOUNCED = 'bounced'
    SPAM = 'spam'
    UNSUBSCRIBED = 'unsubscribed'
    FAILED = 'failed'

class EmailTracking(db.Model):
    __tablename__ = 'email_tracking'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipient_email = db.Column(db.String(120), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'))
    
    # Tracking IDs
    message_id = db.Column(db.String(100), unique=True)
    tracking_pixel_id = db.Column(db.String(100), unique=True)
    
    # Event Tracking
    sent_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    opened_at = db.Column(db.DateTime)
    last_clicked_at = db.Column(db.DateTime)
    
    # Stats
    open_count = db.Column(db.Integer, default=0)
    click_count = db.Column(db.Integer, default=0)
    
    # Status
    is_delivered = db.Column(db.Boolean, default=False)
    is_opened = db.Column(db.Boolean, default=False)
    is_clicked = db.Column(db.Boolean, default=False)
    is_bounced = db.Column(db.Boolean, default=False)
    is_spam = db.Column(db.Boolean, default=False)
    is_unsubscribed = db.Column(db.Boolean, default=False)
    
    # Device/Client Info
    user_agent = db.Column(db.String(200))
    device_type = db.Column(db.String(50))
    client_type = db.Column(db.String(50))
    client_os = db.Column(db.String(50))
    
    # Location Data
    ip_address = db.Column(db.String(45))
    country = db.Column(db.String(2))
    city = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('tracking_events', lazy=True))
    template = db.relationship('EmailTemplate', backref=db.backref('tracking_events', lazy=True))

    def __init__(self, **kwargs):
        super(EmailTracking, self).__init__(**kwargs)
        self.message_id = self.generate_message_id()
        self.tracking_pixel_id = self.generate_tracking_id()

    def track_event(self, event_type: str, metadata: dict = None):
        """Track an email event with enhanced security and validation"""
        try:
            if event_type not in EventType.__members__:
                raise ValueError(f"Invalid event type: {event_type}")
                
            event = EventType[event_type.upper()]
            self.events = self.events or []
            
            # Create event with timestamp and metadata
            event_data = {
                'type': event.value,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            # Add event to tracking
            self.events.append(event_data)
            
            # Update status based on event
            if event == EventType.SENT:
                self.status = 'sent'
            elif event == EventType.DELIVERED:
                self.status = 'delivered'
            elif event == EventType.OPENED:
                self.status = 'opened'
                self.open_count = (self.open_count or 0) + 1
            elif event == EventType.CLICKED:
                self.status = 'clicked'
                self.click_count = (self.click_count or 0) + 1
            elif event == EventType.FAILED:
                self.status = 'failed'
                
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error tracking event: {str(e)}")
            db.session.rollback()
            raise

    def update_client_info(self, user_agent, ip_address):
        """Update client information with enhanced security and tracking"""
        try:
            from user_agents import parse
            from geoip2.database import Reader
            from src.config import Config
            import hashlib
            
            # Parse user agent
            ua = parse(user_agent)
            self.user_agent = user_agent
            self.browser = f"{ua.browser.family} {ua.browser.version_string}"
            self.os = f"{ua.os.family} {ua.os.version_string}"
            self.device = ua.device.family
            
            # Hash IP for privacy
            self.ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()
            
            # Geolocate IP if database exists
            try:
                with Reader(Config.GEOIP_DB_PATH) as reader:
                    response = reader.city(ip_address)
                    self.country = response.country.name
                    self.city = response.city.name
                    self.timezone = response.location.time_zone
            except Exception as e:
                logger.warning(f"GeoIP lookup failed: {str(e)}")
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating client info: {str(e)}")
            self.user_agent = user_agent
            self.ip_address = ip_address
            db.session.commit()

    @staticmethod
    def generate_message_id():
        """Generate a secure, unique message ID"""
        import secrets
        import time
        import base64
        
        # Generate 16 bytes of random data
        random_bytes = secrets.token_bytes(16)
        # Add timestamp for uniqueness
        timestamp = int(time.time()).to_bytes(8, 'big')
        # Combine and encode
        combined = timestamp + random_bytes
        # URL-safe base64 encoding
        message_id = base64.urlsafe_b64encode(combined).decode('ascii')
        return f"msg_{message_id}"

    @staticmethod
    def generate_tracking_id():
        """Generate a secure, unique tracking ID"""
        import secrets
        import time
        import base64
        import hashlib
        
        # Generate 32 bytes of random data
        random_bytes = secrets.token_bytes(32)
        # Add timestamp for uniqueness
        timestamp = int(time.time()).to_bytes(8, 'big')
        # Combine and hash
        combined = timestamp + random_bytes
        hash_obj = hashlib.sha256(combined)
        # URL-safe base64 encoding of first 16 bytes of hash
        tracking_id = base64.urlsafe_b64encode(hash_obj.digest()[:16]).decode('ascii')
        return f"trk_{tracking_id}"

    def to_dict(self):
        """Convert tracking data to dictionary with sensitive data removed"""
        return {
            'id': self.id,
            'template_id': self.template_id,
            'status': self.status,
            'events': self.events,
            'open_count': self.open_count,
            'click_count': self.click_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'browser': self.browser,
            'os': self.os,
            'device': self.device,
            'country': self.country,
            'city': self.city,
            'timezone': self.timezone
        } 