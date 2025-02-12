import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from src.config import Config
from src.models import EmailTemplate

logger = logging.getLogger(__name__)

def send_email(recipient_email: str, template: EmailTemplate, tracking_id: Optional[str] = None) -> bool:
    """
    Send an email using the provided template
    Returns True if successful, False otherwise
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = template.subject
        msg['From'] = Config.SMTP_FROM_EMAIL
        msg['To'] = recipient_email
        
        # Add tracking pixel if tracking enabled
        html_content = template.html_content
        if tracking_id:
            tracking_pixel = f'<img src="{Config.APP_URL}/track/{tracking_id}" width="1" height="1" />'
            html_content = html_content.replace('</body>', f'{tracking_pixel}</body>')
            
        # Add text and HTML parts
        if template.text_content:
            msg.attach(MIMEText(template.text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        # Connect to SMTP server
        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            if Config.SMTP_USE_TLS:
                server.starttls()
            if Config.SMTP_USERNAME and Config.SMTP_PASSWORD:
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
                
            # Send email
            server.send_message(msg)
            
        return True
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False 