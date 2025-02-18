from datetime import datetime
from src.database import db
from bs4 import BeautifulSoup
import re
from typing import List, Dict
import json

class EmailTemplate(db.Model):
    __tablename__ = 'email_templates'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    
    # Template Content
    subject = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text, nullable=False)
    text_content = db.Column(db.Text)  # Plain text fallback
    
    # Template Variables and Blocks
    variables = db.Column(db.JSON, default=dict)
    conditional_blocks = db.Column(db.JSON, default=dict)
    
    # Version Control
    version = db.Column(db.Integer, default=1)
    parent_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'))
    is_latest = db.Column(db.Boolean, default=True)
    
    # Template Settings
    is_active = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=False)
    is_system = db.Column(db.Boolean, default=False)
    
    # Bounce Tracking
    bounce_count = db.Column(db.Integer, default=0)
    last_bounce = db.Column(db.DateTime)
    bounce_reasons = db.Column(db.JSON)
    
    # Template Stats
    use_count = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)
    open_rate = db.Column(db.Float, default=0.0)
    click_rate = db.Column(db.Float, default=0.0)
    spam_score = db.Column(db.Float, default=0.0)
    spam_report = db.Column(db.JSON, default=dict)
    
    # Validation Status
    is_validated = db.Column(db.Boolean, default=False)
    validation_errors = db.Column(db.JSON)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('templates', lazy=True))
    versions = db.relationship('EmailTemplate', 
                             backref=db.backref('parent', remote_side=[id]),
                             lazy='dynamic')

    def __init__(self, **kwargs):
        # Initialize JSON fields with default empty dictionaries
        kwargs.setdefault('variables', {})
        kwargs.setdefault('conditional_blocks', {})
        kwargs.setdefault('validation_errors', {})
        kwargs.setdefault('spam_report', {})
        kwargs.setdefault('bounce_reasons', {})
        super(EmailTemplate, self).__init__(**kwargs)

    def create_new_version(self, html_content: str, subject: str = None) -> 'EmailTemplate':
        """Create a new version of this template"""
        # Set current version as not latest
        self.is_latest = False
        db.session.flush()
        
        # Create new version
        new_version = EmailTemplate(
            user_id=self.user_id,
            name=self.name,
            description=self.description,
            subject=subject or self.subject,
            html_content=html_content,
            version=self.version + 1,
            parent_id=self.id,
            is_latest=True
        )
        
        db.session.add(new_version)
        db.session.commit()
        return new_version

    def record_bounce(self, reason: str = None):
        """Record a bounce for this template"""
        self.bounce_count += 1
        self.last_bounce = datetime.utcnow()
        
        if reason:
            if not self.bounce_reasons:
                self.bounce_reasons = {}
            self.bounce_reasons[reason] = self.bounce_reasons.get(reason, 0) + 1
        
        db.session.commit()

    def get_bounce_stats(self) -> Dict:
        """Get bounce statistics for this template"""
        return {
            'total_bounces': self.bounce_count,
            'last_bounce': self.last_bounce.isoformat() if self.last_bounce else None,
            'bounce_reasons': self.bounce_reasons or {},
            'bounce_rate': (self.bounce_count / self.use_count) if self.use_count > 0 else 0
        }

    def validate(self) -> bool:
        """Validate template HTML, links, and structure"""
        self.validation_errors = {}
        
        try:
            # Parse HTML
            soup = BeautifulSoup(self.html_content, 'html.parser')
            
            # Check basic HTML structure
            if not soup.find('body'):
                self.validation_errors['structure'] = 'Missing <body> tag'
            
            # Validate links
            links = soup.find_all('a')
            for link in links:
                href = link.get('href')
                if not href or not href.startswith(('http://', 'https://', 'mailto:')):
                    self.validation_errors.setdefault('links', []).append(
                        f'Invalid link: {href}'
                    )
            
            # Check for required elements
            if not soup.find('title'):
                self.validation_errors['structure'] = 'Missing <title> tag'
            
            # Validate images
            images = soup.find_all('img')
            for img in images:
                if not img.get('alt'):
                    self.validation_errors.setdefault('images', []).append(
                        f'Missing alt text for image: {img.get("src")}'
                    )
            
            # Check for broken variables
            variables = re.findall(r'\{\{(.*?)\}\}', self.html_content)
            for var in variables:
                if var.strip() not in self.variables:
                    self.validation_errors.setdefault('variables', []).append(
                        f'Undefined variable: {var}'
                    )
            
            self.is_validated = len(self.validation_errors) == 0
            db.session.commit()
            
            return self.is_validated
            
        except Exception as e:
            self.validation_errors['parsing'] = str(e)
            self.is_validated = False
            db.session.commit()
            return False

    def check_spam_score(self) -> float:
        """Calculate spam score based on various factors"""
        score = 0.0
        report = {}
        
        # Check for spam trigger words
        spam_words = ['free', 'guarantee', 'no obligation', 'winner', 'won', 'prize']
        found_words = []
        for word in spam_words:
            if word in self.html_content.lower():
                found_words.append(word)
                score += 0.5
        
        if found_words:
            report['spam_words'] = found_words
        
        # Check for excessive caps
        caps_ratio = sum(1 for c in self.subject if c.isupper()) / len(self.subject)
        if caps_ratio > 0.3:
            score += 0.5
            report['excessive_caps'] = True
        
        # Check for multiple exclamation marks
        if '!!' in self.subject:
            score += 0.3
            report['multiple_exclamations'] = True
        
        # Store results
        self.spam_score = score
        self.spam_report = report
        db.session.commit()
        
        return score

    def render(self, data: Dict = None) -> str:
        """Render template with provided data"""
        content = self.html_content
        
        if data:
            # Replace variables
            for key, value in data.items():
                content = content.replace(f'{{{{{key}}}}}', str(value))
            
            # Process conditional blocks
            for block_id, conditions in self.conditional_blocks.items():
                show_block = eval(conditions['condition'], {"__builtins__": {}}, data)
                if not show_block:
                    content = content.replace(f'<!-- BEGIN {block_id} -->', '<!-- ')
                    content = content.replace(f'<!-- END {block_id} -->', ' -->')
        
        return content

    def get_stats(self) -> Dict:
        """Get template usage statistics"""
        return {
            'use_count': self.use_count,
            'success_rate': self.success_rate,
            'open_rate': self.open_rate,
            'click_rate': self.click_rate,
            'spam_score': self.spam_score
        }

    def update_stats(self, success: bool, opened: bool, clicked: bool):
        """Update template statistics"""
        self.use_count += 1
        
        # Update rates
        if success:
            self.success_rate = ((self.success_rate * (self.use_count - 1)) + 1) / self.use_count
        if opened:
            self.open_rate = ((self.open_rate * (self.use_count - 1)) + 1) / self.use_count
        if clicked:
            self.click_rate = ((self.click_rate * (self.use_count - 1)) + 1) / self.use_count
        
        db.session.commit() 