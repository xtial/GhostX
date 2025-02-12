import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import logging
from src.config import SMTP_CONFIG

logger = logging.getLogger(__name__)

def send_spoofed_email(to_email, from_name, from_email, subject, html_content):
    """
    Send a spoofed email using MailerSend SMTP.
    
    Args:
        to_email (str): Recipient email address
        from_name (str): Display name of the sender
        from_email (str): Email address of the sender (will be replaced with MailerSend address)
        subject (str): Email subject
        html_content (str): HTML content of the email
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        # msg['From'] = formataddr((from_name, from_email))       #change to when you get your a smtp
        sender_email = SMTP_CONFIG['username']  # This is your verified MailerSend email
        msg['From'] = formataddr((from_name, sender_email))

        msg['To'] = to_email
        
        # Add HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Connect to SMTP server with authentication
        with smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port']) as server:
            server.starttls()  # Enable TLS
            server.login(SMTP_CONFIG['username'], SMTP_CONFIG['password'])
            server.send_message(msg)
            
        logger.info(f"Email sent successfully to {to_email} from {from_name} <{sender_email}>")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False 