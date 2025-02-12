import re
import html

def is_password_strong(password: str) -> bool:
    """
    Check if the password meets strong password requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one number
    - Contains at least one special character
    """
    if len(password) < 8:
        return False
    
    if not re.search(r'[A-Z]', password):
        return False
    
    if not re.search(r'[a-z]', password):
        return False
    
    if not re.search(r'\d', password):
        return False
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    
    return True

def sanitize_input(input_str: str) -> str:
    """
    Sanitize user input by escaping HTML special characters and removing potentially dangerous content
    """
    # Escape HTML special characters
    sanitized = html.escape(input_str)
    
    # Remove any script tags and their contents
    sanitized = re.sub(r'<script.*?>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove any other HTML tags
    sanitized = re.sub(r'<.*?>', '', sanitized)
    
    return sanitized.strip()

def validate_username(username: str) -> bool:
    """
    Validate username requirements:
    - Between 3 and 20 characters
    - Only contains alphanumeric characters, underscores, and hyphens
    - Starts with a letter
    """
    if not 3 <= len(username) <= 20:
        return False
    
    if not username[0].isalpha():
        return False
    
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', username):
        return False
    
    return True 