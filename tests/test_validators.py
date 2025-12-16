"""
Tests for validators module.

This module tests the input validation functionality,
including the bug fix for overly aggressive dangerous pattern detection
that was blocking legitimate user input containing common punctuation.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validators import (
    validate_text_input,
    contains_dangerous_patterns,
    sanitize_text_input,
    validate_model_version,
    DANGEROUS_PATTERNS
)


class TestDangerousPatternsFixBug:
    """
    Test cases for the bug fix: overly aggressive dangerous pattern detection.
    
    BUG: The original pattern r'[;&|`$]' blocked legitimate text containing
    semicolons, ampersands, and dollar signs used in normal sentences.
    
    FIX: Modified patterns to be context-aware, only blocking these characters
    when they appear in actual command injection contexts.
    """
    
    def test_semicolon_in_normal_sentence_should_be_allowed(self):
        """
        BUG FIX TEST: Semicolons in normal sentences should NOT be blocked.
        
        Before fix: "I love this product; it's amazing!" would be rejected.
        After fix: This legitimate text should be accepted.
        """
        text = "I love this product; it's amazing and works perfectly fine"
        is_dangerous, _ = contains_dangerous_patterns(text)
        
        assert not is_dangerous, \
            "Bug: Semicolon in normal sentence should not be flagged as dangerous"
    
    def test_ampersand_in_normal_text_should_be_allowed(self):
        """
        BUG FIX TEST: Ampersands in normal text should NOT be blocked.
        
        Before fix: "Tom & Jerry is a great show" would be rejected.
        After fix: This legitimate text should be accepted.
        """
        text = "The R&D department did an amazing job with this product"
        is_dangerous, _ = contains_dangerous_patterns(text)
        
        assert not is_dangerous, \
            "Bug: Ampersand in normal text should not be flagged as dangerous"
    
    def test_dollar_sign_in_price_should_be_allowed(self):
        """
        BUG FIX TEST: Dollar signs in price mentions should NOT be blocked.
        
        Before fix: "This costs $50 and is worth every penny" would be rejected.
        After fix: This legitimate text should be accepted.
        """
        text = "This product costs $50 and is definitely worth every penny"
        is_dangerous, _ = contains_dangerous_patterns(text)
        
        assert not is_dangerous, \
            "Bug: Dollar sign in price should not be flagged as dangerous"
    
    def test_multiple_common_punctuation_should_be_allowed(self):
        """
        BUG FIX TEST: Text with multiple common punctuation should be allowed.
        """
        text = "Great product; costs $25 & ships fast. Tom & Jerry approved!"
        is_dangerous, _ = contains_dangerous_patterns(text)
        
        assert not is_dangerous, \
            "Bug: Multiple common punctuation should not be flagged as dangerous"
    
    def test_validate_text_input_accepts_legitimate_text_with_punctuation(self):
        """
        BUG FIX TEST: Full validation should accept legitimate text with punctuation.
        """
        text = "This is an amazing product; it costs $30 & works great!"
        is_valid, error_msg = validate_text_input(text)
        
        assert is_valid, \
            f"Bug: Legitimate text with punctuation should be valid. Error: {error_msg}"


class TestDangerousPatternsStillBlockThreats:
    """
    Test cases to ensure security patterns still block actual threats.
    """
    
    def test_backtick_command_substitution_blocked(self):
        """Backticks for command substitution should still be blocked."""
        text = "This is a test `whoami` injection attempt here"
        is_dangerous, _ = contains_dangerous_patterns(text)
        
        assert is_dangerous, \
            "Backtick command substitution should be blocked"
    
    def test_command_injection_with_semicolon_blocked(self):
        """Command injection patterns with semicolon should be blocked."""
        text = "Some text here ; rm -rf / dangerous command"
        is_dangerous, _ = contains_dangerous_patterns(text)
        
        assert is_dangerous, \
            "Command injection with semicolon should be blocked"
    
    def test_pipe_to_command_blocked(self):
        """Pipe to command patterns should be blocked."""
        text = "Some input | cat /etc/passwd"
        is_dangerous, _ = contains_dangerous_patterns(text)
        
        assert is_dangerous, \
            "Pipe to command should be blocked"
    
    def test_dollar_command_substitution_blocked(self):
        """Dollar sign command substitution should be blocked."""
        text = "Injecting $(whoami) command here"
        is_dangerous, _ = contains_dangerous_patterns(text)
        
        assert is_dangerous, \
            "Dollar command substitution $() should be blocked"
    
    def test_variable_expansion_blocked(self):
        """Variable expansion patterns should be blocked."""
        text = "Trying to access ${HOME} variable"
        is_dangerous, _ = contains_dangerous_patterns(text)
        
        assert is_dangerous, \
            "Variable expansion ${} should be blocked"
    
    def test_sql_injection_still_blocked(self):
        """SQL injection patterns should still be blocked."""
        text = "SELECT * FROM users WHERE id = 1"
        is_dangerous, _ = contains_dangerous_patterns(text)
        
        assert is_dangerous, \
            "SQL injection should be blocked"
    
    def test_xss_script_tag_still_blocked(self):
        """XSS script tags should still be blocked."""
        text = "Hello <script>alert('xss')</script> world"
        is_dangerous, _ = contains_dangerous_patterns(text)
        
        assert is_dangerous, \
            "XSS script tags should be blocked"
    
    def test_path_traversal_still_blocked(self):
        """Path traversal patterns should still be blocked."""
        text = "Trying to access ../../../etc/passwd"
        is_dangerous, _ = contains_dangerous_patterns(text)
        
        assert is_dangerous, \
            "Path traversal should be blocked"


class TestValidateTextInput:
    """Test cases for validate_text_input function."""
    
    def test_none_input_returns_error(self):
        """None input should return validation error."""
        is_valid, error_msg = validate_text_input(None)
        assert not is_valid
        assert "kosong" in error_msg.lower()
    
    def test_empty_string_returns_error(self):
        """Empty string should return validation error."""
        is_valid, error_msg = validate_text_input("")
        assert not is_valid
        assert "kosong" in error_msg.lower()
    
    def test_whitespace_only_returns_error(self):
        """Whitespace-only string should return validation error."""
        is_valid, error_msg = validate_text_input("   \t\n  ")
        assert not is_valid
        assert "kosong" in error_msg.lower()
    
    def test_non_string_input_returns_error(self):
        """Non-string input should return validation error."""
        is_valid, error_msg = validate_text_input(12345)
        assert not is_valid
        assert "teks" in error_msg.lower()
    
    def test_valid_text_passes_validation(self):
        """Valid text with sufficient words should pass validation."""
        text = "This is a valid input text with more than seven words"
        is_valid, error_msg = validate_text_input(text)
        assert is_valid
        assert error_msg == ""
    
    def test_text_below_min_words_returns_error(self):
        """Text with fewer than minimum words should return error."""
        text = "Too short"
        is_valid, error_msg = validate_text_input(text)
        assert not is_valid
        assert "kata" in error_msg.lower()


class TestValidateModelVersion:
    """Test cases for validate_model_version function."""
    
    def test_valid_version_v1(self):
        """Version v1 should be valid."""
        assert validate_model_version("v1") is True
    
    def test_valid_version_v2(self):
        """Version v2 should be valid."""
        assert validate_model_version("v2") is True
    
    def test_invalid_version_returns_false(self):
        """Invalid version should return False."""
        assert validate_model_version("v3") is False
        assert validate_model_version("invalid") is False
    
    def test_none_version_returns_false(self):
        """None version should return False."""
        assert validate_model_version(None) is False
    
    def test_non_string_version_returns_false(self):
        """Non-string version should return False."""
        assert validate_model_version(123) is False


class TestSanitizeTextInput:
    """Test cases for sanitize_text_input function."""
    
    def test_html_entities_escaped(self):
        """HTML entities should be escaped."""
        text = "<div>Hello</div>"
        sanitized = sanitize_text_input(text)
        assert "&lt;" in sanitized
        assert "&gt;" in sanitized
    
    def test_null_bytes_removed(self):
        """Null bytes should be removed."""
        text = "Hello\x00World"
        sanitized = sanitize_text_input(text)
        assert "\x00" not in sanitized
    
    def test_empty_input_returns_empty(self):
        """Empty input should return empty."""
        assert sanitize_text_input("") == ""
        assert sanitize_text_input(None) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
