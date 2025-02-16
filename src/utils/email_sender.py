import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid, formatdate
from email.header import Header
import logging
from typing import Optional, Dict, Tuple
from src.config import Config
from src.models import EmailTemplate
import dns.resolver
import re
import idna
import html
from bs4 import BeautifulSoup
import bleach
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def validate_email_address(email: str) -> Tuple[bool, str]:
    """Validate email address format and domain"""
    try:
        # Basic format validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return False, "Invalid email format"
            
        # Split email into local part and domain
        local_part, domain = email.rsplit('@', 1)
        
        # Validate local part length
        if len(local_part) > 64:
            return False, "Local part too long"
            
        # Validate domain
        try:
            domain = idna.encode(domain).decode('ascii')
        except Exception:
            return False, "Invalid domain encoding"
            
        # Check MX records
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            if not mx_records:
                return False, "No MX records found"
        except Exception:
            return False, "Could not verify domain MX records"
            
        return True, ""
        
    except Exception as e:
        return False, str(e)

def sanitize_html_content(html_content: str) -> str:
    """Sanitize HTML content to prevent XSS and other injection attacks"""
    try:
        # Define allowed tags and attributes
        allowed_tags = [
            'a', 'b', 'blockquote', 'br', 'div', 'em', 'h1', 'h2', 'h3',
            'h4', 'h5', 'h6', 'i', 'img', 'li', 'ol', 'p', 'span', 'strong',
            'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul'
        ]
        allowed_attrs = {
            '*': ['class', 'style'],
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'width', 'height']
        }
        allowed_styles = [
            'color', 'font-family', 'font-size', 'font-weight', 'margin',
            'padding', 'text-align', 'text-decoration'
        ]
        
        # Clean HTML using bleach
        cleaned_html = bleach.clean(
            html_content,
            tags=allowed_tags,
            attributes=allowed_attrs,
            styles=allowed_styles,
            strip=True
        )
        
        # Parse and validate URLs
        soup = BeautifulSoup(cleaned_html, 'html.parser')
        for tag in soup.find_all(['a', 'img']):
            if 'href' in tag.attrs:
                url = tag['href']
                parsed = urlparse(url)
                if not parsed.scheme:
                    tag['href'] = f"https://{url}"
                elif parsed.scheme not in ['http', 'https', 'mailto']:
                    del tag['href']
            if 'src' in tag.attrs:
                url = tag['src']
                parsed = urlparse(url)
                if not parsed.scheme:
                    tag['src'] = f"https://{url}"
                elif parsed.scheme not in ['http', 'https']:
                    del tag['src']
        
        return str(soup)
        
    except Exception as e:
        logger.error(f"Error sanitizing HTML: {str(e)}")
        # Return text-only version if sanitization fails
        return html.escape(BeautifulSoup(html_content, 'html.parser').get_text())

def send_email(recipient_email: str, template: EmailTemplate, 
               tracking_id: Optional[str] = None) -> bool:
    """
    Send an email using the provided template with enhanced security
    Returns True if successful, False otherwise
    """
    try:
        # Validate recipient email
        is_valid, error = validate_email_address(recipient_email)
        if not is_valid:
            logger.error(f"Invalid recipient email: {error}")
            return False
            
        # Create message
        msg = MIMEMultipart('alternative')
        
        # Set headers with security in mind
        msg['Message-ID'] = make_msgid(domain=Config.SMTP_DOMAIN)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = Header(template.subject, 'utf-8')
        msg['To'] = formataddr(('', recipient_email))
        msg['From'] = formataddr((template.sender_name, Config.SMTP_FROM_EMAIL))
        msg['Reply-To'] = Config.SMTP_REPLY_TO or Config.SMTP_FROM_EMAIL
        
        # Add security headers
        msg['X-Mailer'] = 'GhostX Secure Mailer'
        msg['X-Priority'] = '3'
        
        # Sanitize and prepare content
        html_content = template.html_content
        
        # Add tracking pixel if tracking enabled
        if tracking_id and Config.ENABLE_EMAIL_TRACKING:
            tracking_pixel = (
                f'<img src="{Config.APP_URL}/track/{tracking_id}" '
                'width="1" height="1" style="display:none" />'
            )
            html_content = html_content.replace('</body>', f'{tracking_pixel}</body>')
        
        # Sanitize HTML content
        html_content = sanitize_html_content(html_content)
        
        # Create plain text version
        text_content = BeautifulSoup(html_content, 'html.parser').get_text()
        
        # Add text and HTML parts
        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        # Set up SMTP connection with proper security
        smtp_class = smtplib.SMTP_SSL if Config.SMTP_USE_SSL else smtplib.SMTP
        with smtp_class(Config.SMTP_HOST, Config.SMTP_PORT, 
                       timeout=Config.SMTP_TIMEOUT) as server:
            if not Config.SMTP_USE_SSL and Config.SMTP_USE_TLS:
                server.starttls()
                
            if Config.SMTP_USER and Config.SMTP_PASS:
                server.login(Config.SMTP_USER, Config.SMTP_PASS)
                
            # Send email with proper error handling
            try:
                server.send_message(msg)
                logger.info(f"Email sent successfully to {recipient_email}")
                return True
            except smtplib.SMTPRecipientsRefused:
                logger.error(f"Recipient refused: {recipient_email}")
                return False
            except smtplib.SMTPSenderRefused:
                logger.error("Sender address refused")
                return False
            except smtplib.SMTPDataError as e:
                logger.error(f"SMTP data error: {str(e)}")
                return False
                
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

def parse_email_address(email: str) -> Optional[Dict[str, str]]:
    """Parse email address into components with validation"""
    try:
        if not email or '@' not in email:
            return None
            
        local_part, domain = email.rsplit('@', 1)
        
        # Validate local part
        if not re.match(r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+$', local_part):
            return None
            
        # Handle potential subdirectory
        domain_parts = domain.split('/')
        result = {
            'local_part': local_part,
            'domain': domain_parts[0],
            'type': 'standard'
        }
        
        if len(domain_parts) > 1:
            result['subdirectory'] = domain_parts[1]
            result['type'] = 'subdirectory'
        elif '.' not in domain_parts[0]:
            result['type'] = 'non-tld'
            
        return result
        
    except Exception as e:
        logger.error(f"Error parsing email address: {str(e)}")
        return None

def encode_punycode(domain: str) -> str:
    """Encode domain in Punycode for international support"""
    try:
        return idna.encode(domain).decode('ascii')
    except Exception as e:
        logger.error(f"Error encoding domain: {str(e)}")
        return domain

def test_smtp_connection() -> bool:
    """Test SMTP connection and authentication"""
    try:
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
            if Config.SMTP_USE_TLS:
                server.starttls()
            if Config.SMTP_USER and Config.SMTP_PASS:
                server.login(Config.SMTP_USER, Config.SMTP_PASS)
        return True
    except Exception as e:
        logger.error(f"SMTP test failed: {str(e)}")
        return False

def check_smtp_connection() -> bool:
    """Test SMTP connection"""
    try:
        with smtplib.SMTP(Config.SMTP_CONFIG['host'], Config.SMTP_CONFIG['port']) as server:
            if Config.SMTP_CONFIG['use_tls']:
                server.starttls()
            server.login(Config.SMTP_CONFIG['username'], Config.SMTP_CONFIG['password'])
        return True
    except Exception as e:
        logger.error(f"SMTP connection test failed: {str(e)}")
        return False

def send_email(template: EmailTemplate, to_email: str, from_name: str, from_email: str) -> Tuple[bool, str]:
    """Send an email using a template"""
    try:
        # Validate recipient email
        is_valid, error = validate_email_address(to_email)
        if not is_valid:
            return False, error

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = template.subject
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = to_email
        msg['Date'] = formatdate()
        msg['Message-ID'] = make_msgid()
        
        # Add HTML and plain text parts
        if template.text_content:
            msg.attach(MIMEText(template.text_content, 'plain'))
        msg.attach(MIMEText(template.html_content, 'html'))

        # Send email
        with smtplib.SMTP(Config.SMTP_CONFIG['host'], Config.SMTP_CONFIG['port']) as server:
            if Config.SMTP_CONFIG['use_tls']:
                server.starttls()
            server.login(Config.SMTP_CONFIG['username'], Config.SMTP_CONFIG['password'])
            
            try:
                server.send_message(msg)
                template.update_stats(success=True)
                return True, "Email sent successfully"
            except smtplib.SMTPRecipientsRefused as e:
                # Handle permanent failure
                template.record_bounce("Recipient refused")
                return False, f"Recipient refused: {str(e)}"
            except smtplib.SMTPDataError as e:
                # Handle data-related errors
                template.record_bounce("Data error")
                return False, f"Data error: {str(e)}"
            except smtplib.SMTPSenderRefused as e:
                # Handle sender-related errors
                template.record_bounce("Sender refused")
                return False, f"Sender refused: {str(e)}"
            except Exception as e:
                # Handle other SMTP errors
                template.record_bounce(str(e))
                return False, f"SMTP error: {str(e)}"

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        template.update_stats(success=False)
        return False, f"Error sending email: {str(e)}" 