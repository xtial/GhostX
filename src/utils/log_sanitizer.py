"""Utility functions for sanitizing log messages to prevent log injection."""

import re
import html
from typing import Any, Union

def sanitize_log(message: Any) -> str:
    """
    Sanitize a message for safe logging.
    
    This function:
    1. Converts message to string
    2. Escapes HTML entities
    3. Removes ANSI escape sequences
    4. Removes control characters
    5. Limits line length
    6. Prevents log injection with newlines
    
    Args:
        message: The message to sanitize (can be any type)
        
    Returns:
        str: The sanitized message safe for logging
    """
    # Convert to string if not already
    message = str(message)
    
    # Escape HTML entities
    message = html.escape(message)
    
    # Remove ANSI escape sequences
    message = re.sub(r'\x1b\[[0-9;]*[mGKHF]', '', message)
    
    # Remove control characters except newlines and tabs
    message = ''.join(char for char in message if char.isprintable() or char in '\n\t')
    
    # Replace newlines and tabs with spaces to prevent log injection
    message = message.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    # Limit line length
    if len(message) > 1000:
        message = message[:997] + '...'
        
    return message

def sanitize_user_data(data: Union[str, int, float]) -> str:
    """
    Specifically sanitize user-provided data for logging.
    More strict than general sanitize_log function.
    
    Args:
        data: User-provided data to sanitize
        
    Returns:
        str: Sanitized string safe for logging
    """
    # Convert to string
    data = str(data)
    
    # Remove all special characters
    data = re.sub(r'[^a-zA-Z0-9@._-]', '', data)
    
    # Limit length even more strictly for user data
    if len(data) > 100:
        data = data[:97] + '...'
        
    return data

def sanitize_log_context(context: dict) -> dict:
    """
    Sanitize an entire logging context dictionary.
    
    Args:
        context: Dictionary of values to be logged
        
    Returns:
        dict: Sanitized dictionary safe for logging
    """
    return {
        sanitize_log(k): sanitize_log(v)
        for k, v in context.items()
    }

def create_safe_logger(logger_name: str) -> 'SafeLogger':
    """
    Create a logger wrapper that automatically sanitizes all messages.
    
    Args:
        logger_name: Name for the logger
        
    Returns:
        SafeLogger: A logger that automatically sanitizes messages
    """
    import logging
    
    class SafeLogger:
        def __init__(self, name: str):
            self._logger = logging.getLogger(name)
            
        def _safe_log(self, level: int, msg: Any, *args, **kwargs):
            safe_msg = sanitize_log(msg)
            if kwargs.get('extra'):
                kwargs['extra'] = sanitize_log_context(kwargs['extra'])
            self._logger.log(level, safe_msg, *args, **kwargs)
            
        def debug(self, msg: Any, *args, **kwargs):
            self._safe_log(logging.DEBUG, msg, *args, **kwargs)
            
        def info(self, msg: Any, *args, **kwargs):
            self._safe_log(logging.INFO, msg, *args, **kwargs)
            
        def warning(self, msg: Any, *args, **kwargs):
            self._safe_log(logging.WARNING, msg, *args, **kwargs)
            
        def error(self, msg: Any, *args, **kwargs):
            self._safe_log(logging.ERROR, msg, *args, **kwargs)
            
        def critical(self, msg: Any, *args, **kwargs):
            self._safe_log(logging.CRITICAL, msg, *args, **kwargs)
            
    return SafeLogger(logger_name) 