"""Privacy utility for PII detection and anonymization."""

import re
from typing import Tuple, List

# Regex patterns
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
PHONE_PATTERNS = [
    r'\+?62\s?8\d{2}[\s-]?\d{3,4}[\s-]?\d{3,4}',  # +62812-3456-7890
    r'0\d{2,3}[\s-]?\d{3,4}[\s-]?\d{3,4}',        # 021-1234-5678
    r'\(\d{2,3}\)\s?\d{3,4}[\s-]?\d{3,4}',        # (021) 1234-5678
]


def anonymize_pii(text: str) -> Tuple[str, bool]:
    """
    Anonymize PII by replacing email and phone numbers with placeholders.
    
    Returns:
        Tuple of (anonymized_text, has_pii)
        - Returns ("", False) if text is None or not a string
    """
    if text is None or not isinstance(text, str):
        return "", False
    
    if not text:  # Empty string
        return text, False
    
    anonymized_text = text
    has_pii = False
    
    # Anonymize emails
    if re.search(EMAIL_PATTERN, anonymized_text):
        anonymized_text = re.sub(EMAIL_PATTERN, '[EMAIL]', anonymized_text)
        has_pii = True
    
    # Anonymize phone numbers
    for pattern in PHONE_PATTERNS:
        if re.search(pattern, anonymized_text):
            anonymized_text = re.sub(pattern, '[PHONE]', anonymized_text)
            has_pii = True
    
    return anonymized_text, has_pii


def detect_pii(text: str) -> List[str]:
    """
    Detect types of PII in text.
    
    Returns:
        List of PII types found (e.g., ['email', 'phone'])
    """
    if not text or not isinstance(text, str):
        return []
    
    pii_types = []
    
    if re.search(EMAIL_PATTERN, text):
        pii_types.append('email')
    
    for pattern in PHONE_PATTERNS:
        if re.search(pattern, text):
            pii_types.append('phone')
            break
    
    return pii_types
