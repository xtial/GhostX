from datetime import datetime
from src.database import db
from enum import Enum

class CampaignStatus(Enum):
    DRAFT = 'draft'
    SCHEDULED = 'scheduled'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    PAUSED = 'paused'

class Campaign(db.Model):
    __tablename__ = 'campaigns'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'))
    
    # Campaign Settings
    status = db.Column(db.String(20), default=CampaignStatus.DRAFT.value)
    schedule_time = db.Column(db.DateTime)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    
    # A/B Testing
    is_ab_test = db.Column(db.Boolean, default=False)
    template_b_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'))
    ab_test_ratio = db.Column(db.Float, default=0.5)  # Ratio for template A vs B
    winning_template = db.Column(db.Integer, db.ForeignKey('email_templates.id'))
    
    # Campaign Stats
    total_recipients = db.Column(db.Integer, default=0)
    emails_sent = db.Column(db.Integer, default=0)
    emails_delivered = db.Column(db.Integer, default=0)
    emails_opened = db.Column(db.Integer, default=0)
    emails_clicked = db.Column(db.Integer, default=0)
    emails_failed = db.Column(db.Integer, default=0)
    
    # Rate Limiting
    send_rate = db.Column(db.Integer)  # Emails per hour
    max_daily_emails = db.Column(db.Integer)
    
    # Tracking and Analytics
    tracking_enabled = db.Column(db.Boolean, default=True)
    click_tracking = db.Column(db.Boolean, default=True)
    open_tracking = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('campaigns', lazy=True))
    template = db.relationship('EmailTemplate', foreign_keys=[template_id])
    template_b = db.relationship('EmailTemplate', foreign_keys=[template_b_id])
    
    def __init__(self, **kwargs):
        super(Campaign, self).__init__(**kwargs)
        if not self.send_rate:
            self.send_rate = 10  # Default rate limit
        if not self.max_daily_emails:
            self.max_daily_emails = 100  # Default daily limit

    def get_stats(self):
        return {
            'total_recipients': self.total_recipients,
            'emails_sent': self.emails_sent,
            'delivery_rate': (self.emails_delivered / self.emails_sent * 100) if self.emails_sent > 0 else 0,
            'open_rate': (self.emails_opened / self.emails_delivered * 100) if self.emails_delivered > 0 else 0,
            'click_rate': (self.emails_clicked / self.emails_opened * 100) if self.emails_opened > 0 else 0,
            'failure_rate': (self.emails_failed / self.emails_sent * 100) if self.emails_sent > 0 else 0
        }

    def start(self):
        if self.status != CampaignStatus.SCHEDULED.value:
            return False
        self.status = CampaignStatus.RUNNING.value
        self.start_time = datetime.utcnow()
        db.session.commit()
        return True

    def pause(self):
        if self.status != CampaignStatus.RUNNING.value:
            return False
        self.status = CampaignStatus.PAUSED.value
        db.session.commit()
        return True

    def resume(self):
        if self.status != CampaignStatus.PAUSED.value:
            return False
        self.status = CampaignStatus.RUNNING.value
        db.session.commit()
        return True

    def complete(self):
        self.status = CampaignStatus.COMPLETED.value
        self.end_time = datetime.utcnow()
        db.session.commit()
        return True

    def fail(self, reason=None):
        self.status = CampaignStatus.FAILED.value
        self.end_time = datetime.utcnow()
        # TODO: Log failure reason
        db.session.commit()
        return True 