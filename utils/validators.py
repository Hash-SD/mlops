"""Input validation utility for MLOps Streamlit Text AI application."""

from typing import Tuple
from config.settings import settings


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
