"""
Tests for PredictionService.

This module tests the prediction service functionality,
including the bug fix for missing 'prediction_id' key in error results.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.prediction_service import PredictionService


class TestPredictionServiceErrorResult:
    """Test cases for _error_result method consistency."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db_manager = Mock()
        self.mock_model_loader = Mock()
        self.service = PredictionService(self.mock_db_manager, self.mock_model_loader)
    
    def test_error_result_contains_prediction_id_key(self):
        """
        BUG FIX TEST: Verify that _error_result includes 'prediction_id' key.
        
        This test verifies the fix for the bug where _error_result did not
        include 'prediction_id' key, causing inconsistency with successful
        prediction results.
        """
        error_result = self.service._error_result("Test error message")
        
        # Assert that prediction_id key exists
        assert 'prediction_id' in error_result, \
            "Bug: _error_result should include 'prediction_id' key for API consistency"
        
        # Assert that prediction_id is None for error cases
        assert error_result['prediction_id'] is None, \
            "prediction_id should be None in error results"
    
    def test_error_result_structure_matches_success_result(self):
        """Verify error result has same keys as successful prediction result."""
        error_result = self.service._error_result("Test error")
        
        expected_keys = {'prediction', 'confidence', 'latency', 'metadata', 'error', 'prediction_id'}
        actual_keys = set(error_result.keys())
        
        assert expected_keys == actual_keys, \
            f"Error result keys {actual_keys} should match expected keys {expected_keys}"
    
    def test_error_result_with_latency(self):
        """Verify error result correctly includes latency parameter."""
        latency = 1.5
        error_result = self.service._error_result("Test error", latency=latency)
        
        assert error_result['latency'] == latency
        assert error_result['prediction_id'] is None


class TestPredictionServicePredict:
    """Test cases for predict method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db_manager = Mock()
        self.mock_model_loader = Mock()
        self.service = PredictionService(self.mock_db_manager, self.mock_model_loader)
    
    @patch('services.prediction_service.validate_text_input')
    def test_predict_invalid_input_returns_prediction_id_key(self, mock_validate):
        """
        BUG FIX TEST: Verify predict returns prediction_id key even on validation failure.
        """
        # Mock validation to fail
        mock_validate.return_value = (False, "Input too short")
        
        result = self.service.predict("hi", "v1", True)
        
        # Assert prediction_id key exists even in error case
        assert 'prediction_id' in result, \
            "Bug: predict should return 'prediction_id' key even on validation failure"
        assert result['prediction_id'] is None
        assert result['error'] is not None
    
    @patch('services.prediction_service.validate_text_input')
    @patch('services.prediction_service.validate_model_version')
    def test_predict_invalid_model_version_returns_prediction_id_key(self, mock_model_validate, mock_text_validate):
        """
        BUG FIX TEST: Verify predict returns prediction_id key on invalid model version.
        """
        mock_text_validate.return_value = (True, "")
        mock_model_validate.return_value = False
        
        result = self.service.predict("This is a valid test input text", "invalid_version", True)
        
        assert 'prediction_id' in result, \
            "Bug: predict should return 'prediction_id' key on invalid model version"
        assert result['prediction_id'] is None
        assert result['error'] is not None


class TestPredictionServiceLogPrediction:
    """Test cases for log_prediction method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db_manager = Mock()
        self.mock_model_loader = Mock()
        self.service = PredictionService(self.mock_db_manager, self.mock_model_loader)
    
    @patch('services.prediction_service.anonymize_pii')
    def test_log_prediction_returns_prediction_id(self, mock_anonymize):
        """Verify log_prediction returns prediction_id on success."""
        mock_anonymize.return_value = ("test text", False)
        self.mock_db_manager.insert_user_input.return_value = 1
        self.mock_db_manager.insert_prediction.return_value = 42
        
        result = self.service.log_prediction(
            text="test text",
            prediction="positive",
            confidence=0.95,
            latency=0.1,
            model_version="v1",
            consent=True
        )
        
        assert result == 42, "log_prediction should return prediction_id"
    
    @patch('services.prediction_service.anonymize_pii')
    def test_log_prediction_returns_none_on_failure(self, mock_anonymize):
        """Verify log_prediction returns None on database failure."""
        mock_anonymize.return_value = ("test text", False)
        self.mock_db_manager.insert_user_input.side_effect = Exception("DB Error")
        
        result = self.service.log_prediction(
            text="test text",
            prediction="positive",
            confidence=0.95,
            latency=0.1,
            model_version="v1",
            consent=True
        )
        
        assert result is None, "log_prediction should return None on failure"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
