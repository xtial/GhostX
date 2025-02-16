from datetime import datetime
from src.database import db
from enum import Enum

class EventType(Enum):
    SENT = 'sent'
    DELIVERED = 'delivered'
    OPENED = 'opened'
    CLICKED = 'clicked'
    BOUNCED = 'bounced'
    SPAM = 'spam'
    UNSUBSCRIBED = 'unsubscribed'

class EmailTracking(db.Model):
    __tablename__ = 'email_tracking'

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'))
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
    campaign = db.relationship('Campaign', backref=db.backref('tracking_events', lazy=True))
    user = db.relationship('User', backref=db.backref('tracking_events', lazy=True))
    template = db.relationship('EmailTemplate', backref=db.backref('tracking_events', lazy=True))

    def __init__(self, **kwargs):
        super(EmailTracking, self).__init__(**kwargs)
        self.message_id = self.generate_message_id()
        self.tracking_pixel_id = self.generate_tracking_id()

    def track_event(self, event_type: EventType, metadata=None):
        now = datetime.utcnow()
        
        if event_type == EventType.SENT:
            self.sent_at = now
        elif event_type == EventType.DELIVERED:
            self.delivered_at = now
            self.is_delivered = True
        elif event_type == EventType.OPENED:
            if not self.opened_at:
                self.opened_at = now
            self.is_opened = True
            self.open_count += 1
        elif event_type == EventType.CLICKED:
            self.last_clicked_at = now
            self.is_clicked = True
            self.click_count += 1
        elif event_type == EventType.BOUNCED:
            self.is_bounced = True
        elif event_type == EventType.SPAM:
            self.is_spam = True
        elif event_type == EventType.UNSUBSCRIBED:
            self.is_unsubscribed = True
        
        self.updated_at = now
        
        # Update campaign stats
        if self.campaign:
            if event_type == EventType.DELIVERED:
                self.campaign.emails_delivered += 1
            elif event_type == EventType.OPENED:
                self.campaign.emails_opened += 1
            elif event_type == EventType.CLICKED:
                self.campaign.emails_clicked += 1
            elif event_type in [EventType.BOUNCED, EventType.SPAM]:
                self.campaign.emails_failed += 1
        
        db.session.commit()

    def update_client_info(self, user_agent, ip_address):
        # TODO: Implement user agent parsing and IP geolocation
        self.user_agent = user_agent
        self.ip_address = ip_address
        db.session.commit()

    @staticmethod
    def generate_message_id():
        # TODO: Implement secure message ID generation
        return f"msg_{datetime.utcnow().timestamp()}_{id(datetime.utcnow())}"

    @staticmethod
    def generate_tracking_id():
        # TODO: Implement secure tracking ID generation
        return f"trk_{datetime.utcnow().timestamp()}_{id(datetime.utcnow())}" 