"""
Tests for privacy module.

This module tests the PII detection and anonymization functionality,
including the bug fix for handling None/non-string inputs.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.privacy import anonymize_pii, detect_pii


class TestAnonymizePiiBugFix:
    """
    Test cases for the bug fix: anonymize_pii returning None for None input.
    
    BUG: The original function returned (None, False) when text was None,
    which could cause downstream issues when the result is used in database
    operations expecting a string.
    
    FIX: Modified to return ("", False) for None or non-string inputs,
    ensuring a safe string value is always returned.
    """
    
    def test_none_input_returns_empty_string_not_none(self):
        """
        BUG FIX TEST: None input should return empty string, not None.
        
        Before fix: anonymize_pii(None) returned (None, False)
        After fix: anonymize_pii(None) returns ("", False)
        
        This prevents NoneType errors in downstream database operations.
        """
        result_text, has_pii = anonymize_pii(None)
        
        assert result_text == "", \
            f"Bug: None input should return empty string, got {repr(result_text)}"
        assert has_pii is False, \
            "Bug: None input should return has_pii=False"
        assert isinstance(result_text, str), \
            f"Bug: Result should be string type, got {type(result_text)}"
    
    def test_non_string_input_returns_empty_string(self):
        """
        BUG FIX TEST: Non-string input should return empty string.
        
        Before fix: anonymize_pii(123) returned (123, False) - wrong type!
        After fix: anonymize_pii(123) returns ("", False)
        """
        # Test with integer
        result_text, has_pii = anonymize_pii(123)
        assert result_text == "", \
            f"Bug: Integer input should return empty string, got {repr(result_text)}"
        assert has_pii is False
        
        # Test with list
        result_text, has_pii = anonymize_pii(["test"])
        assert result_text == "", \
            f"Bug: List input should return empty string, got {repr(result_text)}"
        assert has_pii is False
        
        # Test with dict
        result_text, has_pii = anonymize_pii({"key": "value"})
        assert result_text == "", \
            f"Bug: Dict input should return empty string, got {repr(result_text)}"
        assert has_pii is False
    
    def test_empty_string_returns_empty_string(self):
        """Empty string input should return empty string."""
        result_text, has_pii = anonymize_pii("")
        
        assert result_text == ""
        assert has_pii is False


class TestAnonymizePiiNormalOperation:
    """Test cases for normal anonymize_pii operation."""
    
    def test_text_without_pii_unchanged(self):
        """Text without PII should be returned unchanged."""
        text = "This is a normal text without any personal information"
        result_text, has_pii = anonymize_pii(text)
        
        assert result_text == text
        assert has_pii is False
    
    def test_email_anonymized(self):
        """Email addresses should be anonymized."""
        text = "Contact me at john.doe@example.com for more info"
        result_text, has_pii = anonymize_pii(text)
        
        assert "[EMAIL]" in result_text
        assert "john.doe@example.com" not in result_text
        assert has_pii is True
    
    def test_indonesian_phone_number_anonymized(self):
        """Indonesian phone numbers should be anonymized."""
        # Format: +62812-3456-7890
        text = "Hubungi saya di +62812-3456-7890 untuk info lebih lanjut"
        result_text, has_pii = anonymize_pii(text)
        
        assert "[PHONE]" in result_text
        assert "+62812-3456-7890" not in result_text
        assert has_pii is True
    
    def test_landline_phone_number_anonymized(self):
        """Landline phone numbers should be anonymized."""
        # Format: 021-1234-5678
        text = "Telepon kantor kami di 021-1234-5678"
        result_text, has_pii = anonymize_pii(text)
        
        assert "[PHONE]" in result_text
        assert "021-1234-5678" not in result_text
        assert has_pii is True
    
    def test_multiple_pii_anonymized(self):
        """Multiple PII items should all be anonymized."""
        text = "Email: test@example.com, Phone: +6281234567890"
        result_text, has_pii = anonymize_pii(text)
        
        assert "[EMAIL]" in result_text
        assert "[PHONE]" in result_text
        assert "test@example.com" not in result_text
        assert "+6281234567890" not in result_text
        assert has_pii is True


class TestDetectPii:
    """Test cases for detect_pii function."""
    
    def test_none_input_returns_empty_list(self):
        """None input should return empty list."""
        result = detect_pii(None)
        assert result == []
    
    def test_non_string_input_returns_empty_list(self):
        """Non-string input should return empty list."""
        assert detect_pii(123) == []
        assert detect_pii(["test"]) == []
    
    def test_empty_string_returns_empty_list(self):
        """Empty string should return empty list."""
        result = detect_pii("")
        assert result == []
    
    def test_text_without_pii_returns_empty_list(self):
        """Text without PII should return empty list."""
        text = "This is normal text without personal information"
        result = detect_pii(text)
        assert result == []
    
    def test_email_detected(self):
        """Email should be detected."""
        text = "Contact: user@example.com"
        result = detect_pii(text)
        assert "email" in result
    
    def test_phone_detected(self):
        """Phone number should be detected."""
        text = "Call: +6281234567890"
        result = detect_pii(text)
        assert "phone" in result
    
    def test_multiple_pii_types_detected(self):
        """Multiple PII types should be detected."""
        text = "Email: test@test.com, Phone: 021-1234-5678"
        result = detect_pii(text)
        assert "email" in result
        assert "phone" in result


class TestAnonymizePiiIntegrationWithPredictionService:
    """
    Integration test to verify anonymize_pii works correctly
    in the context of prediction_service.log_prediction.
    """
    
    def test_anonymize_pii_result_safe_for_database(self):
        """
        Verify that anonymize_pii result is always safe for database insertion.
        
        This simulates the usage in prediction_service.py:
            processed_text, has_pii = anonymize_pii(text)
            text_to_save = processed_text if has_pii else text
        """
        # Test with None - should not cause issues
        processed_text, has_pii = anonymize_pii(None)
        text_to_save = processed_text if has_pii else (None if processed_text == "" else processed_text)
        
        # The key assertion: processed_text should be a string
        assert isinstance(processed_text, str), \
            "processed_text must be a string for safe database operations"
        
        # Test with valid text containing PII
        processed_text, has_pii = anonymize_pii("Email: test@test.com")
        text_to_save = processed_text if has_pii else "Email: test@test.com"
        
        assert isinstance(text_to_save, str)
        assert "[EMAIL]" in text_to_save


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
