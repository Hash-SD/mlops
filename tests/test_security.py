"""
Security tests for input validation and sanitization.
Tests: XSS prevention, SQL injection prevention, command injection prevention
"""

import pytest
from utils.validators import (
    validate_text_input,
    sanitize_text_input,
    contains_dangerous_patterns
)


class TestInputSanitization:
    """Test input sanitization functions."""
    
    def test_sanitize_html_entities(self):
        """Test HTML entity escaping."""
        malicious = "<script>alert('xss')</script>"
        sanitized = sanitize_text_input(malicious)
        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized
    
    def test_sanitize_null_bytes(self):
        """Test null byte removal."""
        text_with_null = "test\x00injection"
        sanitized = sanitize_text_input(text_with_null)
        assert "\x00" not in sanitized
    
    def test_sanitize_preserves_normal_text(self):
        """Test that normal text is preserved."""
        normal_text = "This is a normal review about a product"
        sanitized = sanitize_text_input(normal_text)
        assert sanitized == normal_text


class TestDangerousPatternDetection:
    """Test detection of dangerous patterns."""
    
    def test_detect_script_tags(self):
        """Test XSS script tag detection."""
        xss_attempt = "<script>alert('xss')</script>"
        is_dangerous, _ = contains_dangerous_patterns(xss_attempt)
        assert is_dangerous is True
    
    def test_detect_javascript_protocol(self):
        """Test JavaScript protocol detection."""
        js_attempt = "javascript:alert('xss')"
        is_dangerous, _ = contains_dangerous_patterns(js_attempt)
        assert is_dangerous is True
    
    def test_detect_event_handlers(self):
        """Test event handler detection."""
        event_attempt = "onclick=alert('xss')"
        is_dangerous, _ = contains_dangerous_patterns(event_attempt)
        assert is_dangerous is True
    
    def test_detect_sql_injection(self):
        """Test SQL injection detection."""
        sql_attempts = [
            "SELECT * FROM users WHERE id=1",
            "'; DROP TABLE users; --",
            "UNION SELECT password FROM users",
        ]
        for attempt in sql_attempts:
            is_dangerous, _ = contains_dangerous_patterns(attempt)
            assert is_dangerous is True, f"Failed to detect: {attempt}"
    
    def test_detect_command_injection(self):
        """Test command injection character detection."""
        cmd_attempts = [
            "test; rm -rf /",
            "test | cat /etc/passwd",
            "test `whoami`",
            "test $HOME",
        ]
        for attempt in cmd_attempts:
            is_dangerous, _ = contains_dangerous_patterns(attempt)
            assert is_dangerous is True, f"Failed to detect: {attempt}"
    
    def test_detect_path_traversal(self):
        """Test path traversal detection."""
        path_attempts = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
        ]
        for attempt in path_attempts:
            is_dangerous, _ = contains_dangerous_patterns(attempt)
            assert is_dangerous is True, f"Failed to detect: {attempt}"
    
    def test_allow_safe_text(self):
        """Test that safe text is allowed."""
        safe_texts = [
            "This product is amazing and I love it very much",
            "The service was terrible and I am very disappointed",
            "Produk ini sangat bagus dan saya sangat puas sekali",
        ]
        for text in safe_texts:
            is_dangerous, _ = contains_dangerous_patterns(text)
            assert is_dangerous is False, f"False positive for: {text}"


class TestValidateTextInputSecurity:
    """Test validate_text_input with security checks."""
    
    def test_reject_xss_attempt(self):
        """Test that XSS attempts are rejected."""
        xss_text = "<script>alert('xss')</script> with seven words here now"
        is_valid, error = validate_text_input(xss_text)
        assert is_valid is False
        assert "tidak diizinkan" in error.lower()
    
    def test_reject_sql_injection(self):
        """Test that SQL injection attempts are rejected."""
        sql_text = "SELECT * FROM users WHERE id equals one two three"
        is_valid, error = validate_text_input(sql_text)
        assert is_valid is False
    
    def test_accept_safe_input(self):
        """Test that safe input is accepted."""
        safe_text = "This is a completely safe review about a product"
        is_valid, error = validate_text_input(safe_text)
        assert is_valid is True
        assert error == ""
