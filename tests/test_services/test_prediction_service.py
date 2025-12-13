"""
Unit tests untuk PredictionService
Tests: prediction flow, validation, error handling, logging
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from services.prediction_service import PredictionService
from config.settings import settings


@pytest.fixture
def mock_db_manager():
    """Create mock DatabaseManager"""
    mock = Mock()
    mock.insert_user_input.return_value = 1
    mock.insert_prediction.return_value = 1
    return mock


@pytest.fixture
def mock_model_loader():
    """Create mock ModelLoader"""
    mock = Mock()
    
    # Mock model function yang return prediction dan confidence
    def mock_predict(text):
        return ("positif", 0.85)
    
    mock.load_model.return_value = mock_predict
    mock.get_model_metadata.return_value = {
        'name': 'Test Model',
        'accuracy': 0.85,
        'f1_score': 0.83
    }
    
    return mock


@pytest.fixture
def prediction_service(mock_db_manager, mock_model_loader):
    """Create PredictionService instance dengan mocked dependencies"""
    return PredictionService(mock_db_manager, mock_model_loader)


class TestPredictionValidation:
    """Test input validation"""
    
    def test_validate_input_valid(self, prediction_service):
        """Test validation dengan valid input (minimal 7 kata)"""
        text = "This is a valid test input with seven words here"
        
        is_valid, error_msg = prediction_service.validate_input(text)
        
        assert is_valid is True
        assert error_msg == ""
    
    def test_validate_input_too_short(self, prediction_service):
        """Test validation dengan input terlalu pendek (kurang dari 7 kata)"""
        text = "Only five words here now"  # 5 words, less than 7
        
        is_valid, error_msg = prediction_service.validate_input(text)
        
        assert is_valid is False
        assert "minimal" in error_msg.lower()
    
    def test_validate_input_empty(self, prediction_service):
        """Test validation dengan empty input"""
        text = ""
        
        is_valid, error_msg = prediction_service.validate_input(text)
        
        assert is_valid is False


class TestPredictionFlow:
    """Test main prediction flow"""
    
    def test_predict_success_with_consent(self, prediction_service, mock_db_manager):
        """Test successful prediction dengan user consent"""
        text = "Test input for prediction with more than seven words here"
        model_version = "v1"
        user_consent = True
        
        result = prediction_service.predict(text, model_version, user_consent)
        
        assert result['prediction'] == "positif"
        assert result['confidence'] == 0.85
        assert result['latency'] >= 0  # Can be 0 with mocked fast execution
        assert result['error'] is None
        assert 'metadata' in result
        
        # Verify database logging was called
        mock_db_manager.insert_user_input.assert_called_once()
        mock_db_manager.insert_prediction.assert_called_once()
    
    def test_predict_success_without_consent(self, prediction_service, mock_db_manager):
        """Test successful prediction tanpa user consent"""
        text = "Test input without consent but with more than seven words"
        model_version = "v1"
        user_consent = False
        
        result = prediction_service.predict(text, model_version, user_consent)
        
        assert result['prediction'] == "positif"
        assert result['confidence'] == 0.85
        assert result['error'] is None
        
        # Verify database logging was NOT called
        mock_db_manager.insert_user_input.assert_not_called()
        mock_db_manager.insert_prediction.assert_not_called()
    
    def test_predict_invalid_input(self, prediction_service):
        """Test prediction dengan invalid input"""
        text = "ab"  # Too short
        model_version = "v1"
        user_consent = True
        
        result = prediction_service.predict(text, model_version, user_consent)
        
        assert result['prediction'] is None
        assert result['confidence'] == 0.0
        assert result['error'] is not None
    
    def test_predict_invalid_model_version(self, prediction_service):
        """Test prediction dengan invalid model version"""
        text = "Valid test input with more than seven words here now"
        model_version = "invalid_version"
        user_consent = True
        
        result = prediction_service.predict(text, model_version, user_consent)
        
        assert result['prediction'] is None
        assert result['error'] is not None
        assert "tidak valid" in result['error'].lower()
    
    def test_predict_all_model_versions(self, prediction_service):
        """Test prediction dengan semua valid model versions dari settings"""
        text = "Test input for all versions with more than seven words"
        user_consent = False
        
        # Use MODEL_VERSIONS from settings instead of hardcoded list
        valid_versions = settings.MODEL_VERSIONS
        
        for version in valid_versions:
            result = prediction_service.predict(text, version, user_consent)
            
            assert result['prediction'] is not None, f"Prediction failed for version {version}"
            assert result['error'] is None, f"Error for version {version}: {result['error']}"


class TestPredictionLogging:
    """Test prediction logging ke database"""
    
    def test_log_prediction_success(self, prediction_service, mock_db_manager):
        """Test successful logging"""
        result = prediction_service.log_prediction(
            text="Test text",
            prediction="positif",
            confidence=0.85,
            latency=0.234,
            model_version="v1",
            consent=True
        )
        
        assert result is True
        mock_db_manager.insert_user_input.assert_called_once()
        mock_db_manager.insert_prediction.assert_called_once()
    
    def test_log_prediction_with_pii(self, prediction_service, mock_db_manager):
        """Test logging dengan PII detection"""
        text_with_pii = "Contact me at test@example.com or 08123456789"
        
        result = prediction_service.log_prediction(
            text=text_with_pii,
            prediction="positif",
            confidence=0.85,
            latency=0.234,
            model_version="v1",
            consent=True
        )
        
        assert result is True
        
        # Verify text was anonymized before saving
        call_args = mock_db_manager.insert_user_input.call_args
        saved_text = call_args[1]['text']
        
        # PII should be anonymized
        assert "test@example.com" not in saved_text or "[EMAIL]" in saved_text
    
    def test_log_prediction_database_error(self, prediction_service, mock_db_manager):
        """Test logging dengan database error"""
        mock_db_manager.insert_user_input.side_effect = Exception("Database error")
        
        result = prediction_service.log_prediction(
            text="Test text",
            prediction="positif",
            confidence=0.85,
            latency=0.234,
            model_version="v1",
            consent=True
        )
        
        assert result is False


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_predict_model_loading_error(self, prediction_service, mock_model_loader):
        """Test prediction dengan model loading error"""
        mock_model_loader.load_model.side_effect = Exception("Model loading failed")
        
        result = prediction_service.predict("Test input with more than seven words here now", "v1", False)
        
        assert result['prediction'] is None
        assert result['error'] is not None
        assert "error" in result['error'].lower()
    
    def test_predict_preprocessing_error(self, prediction_service):
        """Test prediction dengan preprocessing error"""
        # Use extremely long text that might cause issues (but still 7+ words)
        text = "word " * 10000
        
        result = prediction_service.predict(text, "v1", False)
        
        # Should handle gracefully
        assert 'error' in result
    
    def test_predict_database_error_continues(self, prediction_service, mock_db_manager):
        """Test prediction continues despite database error"""
        mock_db_manager.insert_user_input.side_effect = Exception("DB error")
        
        result = prediction_service.predict("Test input with more than seven words here now", "v1", True)
        
        # Prediction should still succeed
        assert result['prediction'] is not None
        assert result['error'] is None
        # But should have warning in metadata
        assert 'database_warning' in result['metadata']


class TestMetadataHandling:
    """Test metadata handling"""
    
    def test_metadata_includes_model_info(self, prediction_service):
        """Test metadata includes model information"""
        result = prediction_service.predict("Test input with more than seven words here now", "v1", False)
        
        assert 'metadata' in result
        assert 'name' in result['metadata']
        assert 'accuracy' in result['metadata']
    
    def test_metadata_includes_input_token_count(self, prediction_service):
        """Test metadata includes input token count"""
        result = prediction_service.predict("Test input with more than seven words here now", "v1", False)
        
        assert 'metadata' in result
        assert 'input_token_count' in result['metadata']
        assert result['metadata']['input_token_count'] == 9  # 9 words


class TestSinglePreprocessing:
    """Test that text is only preprocessed once (inside model, not in service)"""
    
    def test_raw_text_passed_to_model(self, mock_db_manager, mock_model_loader):
        """
        Verify that PredictionService passes raw text to model_func,
        NOT preprocessed text. Preprocessing should happen inside the model.
        
        This test verifies the fix for the double preprocessing bug.
        """
        captured_text = []
        
        def mock_predict_capture(text):
            captured_text.append(text)
            return ("positif", 0.85)
        
        mock_model_loader.load_model.return_value = mock_predict_capture
        
        service = PredictionService(mock_db_manager, mock_model_loader)
        
        # Input with mixed case and special chars - should NOT be preprocessed by service (7+ words)
        original_text = "This is a TEST with UPPERCASE and special chars here!"
        
        service.predict(original_text, "v1", False)
        
        # The text passed to model should be the ORIGINAL text, not preprocessed
        assert len(captured_text) == 1
        assert captured_text[0] == original_text, \
            f"Expected raw text '{original_text}', but got '{captured_text[0]}'. " \
            "Text should not be preprocessed by PredictionService."
    
    def test_no_double_preprocessing(self, mock_db_manager, mock_model_loader):
        """
        Ensure text is not cleaned/lowercased before being passed to model.
        The model handles its own preprocessing internally.
        """
        captured_text = []
        
        def mock_predict_capture(text):
            captured_text.append(text)
            return ("negatif", 0.75)
        
        mock_model_loader.load_model.return_value = mock_predict_capture
        
        service = PredictionService(mock_db_manager, mock_model_loader)
        
        # Text with uppercase - if double preprocessing existed, this would be lowercased (7+ words)
        test_text = "UPPERCASE TEXT HERE WITH MORE THAN SEVEN WORDS"
        
        service.predict(test_text, "v1", False)
        
        # Verify uppercase is preserved (not preprocessed by service)
        assert captured_text[0] == "UPPERCASE TEXT HERE WITH MORE THAN SEVEN WORDS"
