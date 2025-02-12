import re
import html
import bleach

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
    Sanitize user input by using bleach library for robust HTML sanitization.
    This provides better protection against XSS attacks compared to regex-based approaches.
    """
    if not isinstance(input_str, str):
        input_str = str(input_str)

    # First, escape all HTML
    escaped = html.escape(input_str)
    
    # Use bleach to strip all HTML tags and attributes
    # This is more robust than regex-based approaches
    cleaned = bleach.clean(
        escaped,
        tags=[],  # No allowed tags
        attributes={},  # No allowed attributes
        protocols=[],  # No allowed protocols
        strip=True,  # Strip disallowed tags
        strip_comments=True  # Strip comments
    )
    
    return cleaned.strip()

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