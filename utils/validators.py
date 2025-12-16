"""Input validation utility for MLOps Streamlit Text AI application."""

import re
import html
from typing import Tuple
from config.settings import settings

# Security: Dangerous patterns to block (SQL injection, XSS, command injection)
DANGEROUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',  # XSS script tags
    r'javascript:',                 # JavaScript protocol
    r'on\w+\s*=',                   # Event handlers (onclick, onerror, etc.)
    r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b.*\b(FROM|INTO|TABLE|WHERE)\b)',  # SQL injection
    r'[`]',                         # Backtick (command substitution)
    r';\s*\w+\s*-',                 # Command injection pattern (e.g., "; rm -")
    r'\|\s*\w+',                    # Pipe to command (e.g., "| cat")
    r'\$\([^)]+\)',                 # Command substitution $(...)
    r'\$\{[^}]+\}',                 # Variable expansion ${...}
    r'\.\./|\.\.\\',               # Path traversal
]


def sanitize_text_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.
    
    Security: Escapes HTML entities and removes dangerous patterns.
    """
    if not text:
        return text
    
    # HTML escape to prevent XSS
    sanitized = html.escape(text)
    
    # Remove null bytes (security risk)
    sanitized = sanitized.replace('\x00', '')
    
    return sanitized


def contains_dangerous_patterns(text: str) -> Tuple[bool, str]:
    """
    Check if text contains potentially dangerous patterns.
    
    Security: Detects SQL injection, XSS, and command injection attempts.
    """
    if not text:
        return False, ""
    
    text_lower = text.lower()
    
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
            return True, "Input mengandung karakter atau pola yang tidak diizinkan"
    
    return False, ""


def validate_text_input(text: str) -> Tuple[bool, str]:
    """
    Validate input text based on length and word count constraints.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if text is None:
        return False, "Input teks tidak boleh kosong"
    
    if not isinstance(text, str):
        return False, "Input harus berupa teks"
    
    text_stripped = text.strip()
    
    if not text_stripped:
        return False, "Input teks tidak boleh kosong"
    
    # Security: Check for dangerous patterns (SQL injection, XSS, etc.)
    is_dangerous, danger_msg = contains_dangerous_patterns(text_stripped)
    if is_dangerous:
        return False, danger_msg
    
    if len(text_stripped) < settings.MIN_INPUT_LENGTH:
        return False, f"Input teks minimal {settings.MIN_INPUT_LENGTH} karakter"
    
    if len(text_stripped) > settings.MAX_INPUT_LENGTH:
        return False, f"Input teks maksimal {settings.MAX_INPUT_LENGTH} karakter"
    
    word_count = len(text_stripped.split())
    if word_count < settings.MIN_WORDS:
        return False, f"Input teks minimal {settings.MIN_WORDS} kata (saat ini: {word_count} kata)"
    
    return True, ""


def validate_model_version(version: str) -> bool:
    """Validate if model version is in the list of valid versions."""
    if version is None or not isinstance(version, str):
        return False
    return version in settings.MODEL_VERSIONS
