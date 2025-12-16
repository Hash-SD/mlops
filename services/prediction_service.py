"""Prediction service for orchestrating prediction flow."""

import time
import logging
from typing import Dict, Any, Tuple

from database.db_manager import DatabaseManager
from models.model_loader import ModelLoader
from utils.validators import validate_text_input, validate_model_version
from utils.privacy import anonymize_pii


class PredictionService:
    """Service for orchestrating prediction flow from input validation to database logging."""
    
    def __init__(self, db_manager: DatabaseManager, model_loader: ModelLoader):
        self.db_manager = db_manager
        self.model_loader = model_loader
        self.logger = logging.getLogger(__name__)
    
    def validate_input(self, text: str) -> Tuple[bool, str]:
        """Validate input text."""
        return validate_text_input(text)
    
    def predict(self, text: str, model_version: str, user_consent: bool) -> Dict[str, Any]:
        """
        Main orchestrator for prediction flow.
        
        Flow:
        1. Validate input
        2. Load model
        3. Predict (preprocessing handled by model)
        4. Measure latency
        5. Log to database (if consent)
        6. Return results
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting prediction with model {model_version}")
            
            # Step 1: Validate input
            is_valid, error_message = self.validate_input(text)
            if not is_valid:
                self.logger.warning(f"Input validation failed: {error_message}")
                return self._error_result(error_message)
            
            if not validate_model_version(model_version):
                error_msg = f"Versi model tidak valid: {model_version}"
                self.logger.warning(error_msg)
                return self._error_result(error_msg)
            
            # Step 2: Load model
            model_func = self.model_loader.load_model(model_version)
            
            # Step 3: Predict (preprocessing is handled inside model_func)
            prediction, confidence = model_func(text)
            
            # Step 4: Measure latency
            latency = time.time() - start_time
            
            # Step 5: Get model metadata
            metadata = self.model_loader.get_model_metadata(model_version)
            metadata['input_token_count'] = len(text.split())
            
            # Step 6: Log to database
            prediction_id = None
            if user_consent:
                prediction_id = self.log_prediction(text, prediction, confidence, latency, model_version, user_consent)
                if not prediction_id:
                    metadata['database_warning'] = "Gagal menyimpan ke database"
            else:
                self.logger.info("User opted out, skipping database logging")
                metadata['database_info'] = "Data tidak disimpan (pilihan user)"
            
            result = {
                'prediction': prediction,
                'confidence': confidence,
                'latency': latency,
                'metadata': metadata,
                'error': None,
                'prediction_id': prediction_id
            }
            
            self.logger.info(f"Prediction completed: {prediction} (confidence: {confidence:.2f}, latency: {latency:.3f}s)")
            return result
            
        except Exception as e:
            latency = time.time() - start_time
            error_msg = f"Error saat melakukan prediksi: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return self._error_result(error_msg, latency)
    
    def _error_result(self, error_message: str, latency: float = 0.0) -> Dict[str, Any]:
        """Create error result dictionary."""
        return {
            'prediction': None,
            'confidence': 0.0,
            'latency': latency,
            'metadata': {},
            'error': error_message,
            'prediction_id': None
        }
    
    def log_prediction(
        self,
        text: str,
        prediction: str,
        confidence: float,
        latency: float,
        model_version: str,
        consent: bool
    ) -> int:
        """
        Log prediction to database.
        
        Returns:
            int: prediction_id if successful, None otherwise
        """
        try:
            # Check for PII and anonymize if needed
            processed_text, has_pii = anonymize_pii(text)
            text_to_save = processed_text if has_pii else text
            
            if has_pii:
                self.logger.info("PII detected and anonymized before saving")
            
            # Insert user input
            input_id = self.db_manager.insert_user_input(text=text_to_save, consent=consent)
            
            # Insert prediction
            prediction_id = self.db_manager.insert_prediction(
                input_id=input_id,
                model_version=model_version,
                prediction=prediction,
                confidence=confidence,
                latency=latency
            )
            
            self.logger.info(f"Prediction logged: input_id={input_id}, prediction_id={prediction_id}, anonymized={has_pii}")
            return prediction_id
            
        except Exception as e:
            self.logger.error(f"Failed to log prediction: {e}", exc_info=True)
            return None
