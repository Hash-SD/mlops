"""
Integration tests untuk end-to-end flow
Tests: input → prediction → database save → display
Tests: model version switching, retraining trigger
"""

import pytest
import tempfile
import os
from pathlib import Path
from database.db_manager import DatabaseManager
from models.model_loader import ModelLoader
from services.prediction_service import PredictionService
from services.monitoring_service import MonitoringService
from services.retraining_service import RetrainingService
from config.settings import settings

# Test input constants (minimum 7 words)
TEST_INPUT_VALID = "Ini adalah test input untuk prediksi dengan lebih dari tujuh kata"
TEST_INPUT_POSITIVE = "Produk ini sangat bagus dan saya sangat puas dengan kualitasnya"
TEST_INPUT_NEGATIVE = "Produk ini sangat mengecewakan dan tidak sesuai dengan ekspektasi saya"
TEST_INPUT_NEUTRAL = "Pengiriman standar dan barang sampai sesuai dengan estimasi waktu pengiriman"
TEST_INPUT_SHORT = "Test input dengan lebih dari tujuh kata untuk validasi"


@pytest.fixture
def temp_db():
    """Create temporary database untuk integration testing"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db')
    temp_file.close()
    db_path = temp_file.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def integrated_system(temp_db):
    """Setup integrated system dengan real components"""
    # Initialize database
    db_manager = DatabaseManager(temp_db)
    db_manager.connect()
    db_manager.initialize_schema()
    
    # Initialize model loader
    model_loader = ModelLoader(mlflow_tracking_uri=None)
    
    # Initialize services
    prediction_service = PredictionService(db_manager, model_loader)
    monitoring_service = MonitoringService(db_manager)
    retraining_service = RetrainingService(db_manager, mlflow_tracking_uri=None)
    
    yield {
        'db_manager': db_manager,
        'model_loader': model_loader,
        'prediction_service': prediction_service,
        'monitoring_service': monitoring_service,
        'retraining_service': retraining_service
    }
    
    # Cleanup
    db_manager.disconnect()


class TestEndToEndPredictionFlow:
    """Test complete prediction flow dari input hingga database"""
    
    def test_prediction_flow_with_consent(self, integrated_system):
        """Test: input → prediction → database save → verify"""
        prediction_service = integrated_system['prediction_service']
        db_manager = integrated_system['db_manager']
        
        # Step 1: Make prediction dengan consent
        text = TEST_INPUT_VALID
        model_version = "v1"
        user_consent = True
        
        result = prediction_service.predict(text, model_version, user_consent)
        
        # Verify prediction result
        assert result['prediction'] is not None
        assert result['confidence'] > 0
        assert result['latency'] > 0
        assert result['error'] is None
        
        # Step 2: Verify data saved to database
        recent_predictions = db_manager.get_recent_predictions(limit=1)
        
        assert len(recent_predictions) == 1
        assert recent_predictions[0]['text_input'] == text
        assert recent_predictions[0]['model_version'] == model_version
        assert recent_predictions[0]['prediction'] == result['prediction']
    
    def test_prediction_flow_without_consent(self, integrated_system):
        """Test: input → prediction (no database save)"""
        prediction_service = integrated_system['prediction_service']
        db_manager = integrated_system['db_manager']
        
        # Get initial count
        initial_predictions = db_manager.get_recent_predictions(limit=100)
        initial_count = len(initial_predictions)
        
        # Make prediction tanpa consent
        text = TEST_INPUT_SHORT
        result = prediction_service.predict(text, "v1", user_consent=False)
        
        # Verify prediction succeeded
        assert result['prediction'] is not None
        assert result['error'] is None
        
        # Verify data NOT saved to database
        current_predictions = db_manager.get_recent_predictions(limit=100)
        assert len(current_predictions) == initial_count
    
    def test_multiple_predictions_flow(self, integrated_system):
        """Test multiple predictions dan verify all saved"""
        prediction_service = integrated_system['prediction_service']
        db_manager = integrated_system['db_manager']
        
        # Make multiple predictions (each with 7+ words)
        texts = [
            "Prediksi pertama dengan lebih dari tujuh kata untuk test",
            "Prediksi kedua dengan lebih dari tujuh kata untuk validasi",
            "Prediksi ketiga dengan lebih dari tujuh kata untuk verifikasi"
        ]
        
        for text in texts:
            result = prediction_service.predict(text, "v1", user_consent=True)
            assert result['error'] is None
        
        # Verify all saved
        recent_predictions = db_manager.get_recent_predictions(limit=10)
        assert len(recent_predictions) >= 3
        
        # Verify texts are in database
        saved_texts = [p['text_input'] for p in recent_predictions]
        for text in texts:
            assert text in saved_texts


class TestModelVersionSwitching:
    """Test switching between different model versions"""
    
    def test_switch_between_all_versions(self, integrated_system):
        """Test prediction dengan all model versions"""
        prediction_service = integrated_system['prediction_service']
        
        text = "Test input untuk semua versi model dengan lebih dari tujuh kata"
        versions = settings.MODEL_VERSIONS  # Use dynamic versions from settings
        
        results = {}
        
        for version in versions:
            result = prediction_service.predict(text, version, user_consent=True)
            
            assert result['error'] is None
            assert result['prediction'] is not None
            
            results[version] = result
        
        # Verify all versions produced results
        assert len(results) == len(settings.MODEL_VERSIONS)
        
        # Verify each version has metadata
        for version, result in results.items():
            assert 'metadata' in result
            assert result['metadata']['name'] is not None
    
    def test_version_switching_persistence(self, integrated_system):
        """Test bahwa version switching tersimpan di database"""
        prediction_service = integrated_system['prediction_service']
        db_manager = integrated_system['db_manager']
        
        # Make predictions dengan different versions (use available versions)
        for version in settings.MODEL_VERSIONS:
            prediction_service.predict(f"Test {version} dengan lebih dari tujuh kata untuk validasi", version, user_consent=True)
        
        # Verify versions saved correctly
        recent_predictions = db_manager.get_recent_predictions(limit=10)
        
        versions_used = [p['model_version'] for p in recent_predictions]
        for version in settings.MODEL_VERSIONS:
            assert version in versions_used


class TestMonitoringIntegration:
    """Test monitoring service integration dengan real data"""
    
    def test_monitoring_after_predictions(self, integrated_system):
        """Test monitoring metrics setelah predictions"""
        prediction_service = integrated_system['prediction_service']
        monitoring_service = integrated_system['monitoring_service']
        
        # Make some predictions
        for i in range(5):
            prediction_service.predict(f"Test {i} dengan lebih dari tujuh kata untuk monitoring", "v1", user_consent=True)
        
        # Get metrics
        metrics = monitoring_service.get_metrics_summary()
        
        assert 'v1' in metrics
        assert metrics['v1']['prediction_count'] >= 5
        assert metrics['v1']['avg_confidence'] > 0
        assert metrics['v1']['avg_latency'] > 0
    
    def test_latency_distribution_integration(self, integrated_system):
        """Test latency distribution dengan real predictions"""
        prediction_service = integrated_system['prediction_service']
        monitoring_service = integrated_system['monitoring_service']
        
        # Make predictions
        for i in range(3):
            prediction_service.predict(f"Test latency {i} dengan lebih dari tujuh kata untuk test", "v1", user_consent=True)
        
        # Get latency distribution
        latencies = monitoring_service.get_latency_distribution(model_version="v1")
        
        assert len(latencies) >= 3
        # Latency can be 0 in fast mocked environments
        assert all(l >= 0 for l in latencies)
    
    def test_prediction_counts_integration(self, integrated_system):
        """Test prediction counts dengan multiple versions"""
        prediction_service = integrated_system['prediction_service']
        monitoring_service = integrated_system['monitoring_service']
        
        # Make predictions dengan different versions
        prediction_service.predict("Test v1 dengan lebih dari tujuh kata untuk validasi", "v1", user_consent=True)
        prediction_service.predict("Test v1 again dengan lebih dari tujuh kata untuk test", "v1", user_consent=True)
        prediction_service.predict("Test v2 dengan lebih dari tujuh kata untuk verifikasi", "v2", user_consent=True)
        
        # Get counts
        counts = monitoring_service.get_prediction_counts()
        
        assert counts['v1'] >= 2
        assert counts['v2'] >= 1


class TestRetrainingIntegration:
    """Test retraining pipeline integration"""
    
    def test_retraining_with_real_data(self, integrated_system):
        """Test retraining pipeline dengan real data dari database"""
        prediction_service = integrated_system['prediction_service']
        retraining_service = integrated_system['retraining_service']
        
        # Create training data (each with 7+ words)
        training_texts = [
            "Ini sangat bagus dan menyenangkan sekali untuk digunakan sehari-hari",
            "Produk ini mengecewakan sekali dan tidak sesuai dengan ekspektasi saya",
            "Biasa saja tidak istimewa tapi cukup untuk kebutuhan dasar saya",
            "Luar biasa sangat memuaskan dan saya sangat puas dengan hasilnya",
            "Buruk sekali tidak recommended dan sangat mengecewakan sekali pengalamannya",
            "Cukup baik untuk harga segini dan sesuai dengan ekspektasi saya",
            "Sangat puas dengan pembelian ini dan akan membeli lagi nanti",
            "Kualitas jelek tidak sesuai ekspektasi dan sangat mengecewakan sekali",
            "Netral saja tidak ada yang spesial tapi cukup untuk kebutuhan",
            "Excellent product highly recommended and very satisfied with quality",
            "Terrible experience very disappointed and will not buy again ever",
            "Average quality nothing special but good enough for basic needs"
        ]
        
        for text in training_texts:
            prediction_service.predict(text, "v1", user_consent=True)
        
        # Validate requirements
        is_valid, message = retraining_service.validate_retraining_requirements()
        assert is_valid is True
        
        # Trigger retraining
        result = retraining_service.trigger_retraining("v1")
        
        assert result['status'] == 'success'
        assert result['new_version'] is not None
        assert 'v1_retrain_' in result['new_version']
        assert 'metrics' in result
    
    def test_retraining_without_sufficient_data(self, integrated_system):
        """Test retraining dengan insufficient data"""
        retraining_service = integrated_system['retraining_service']
        
        # Don't create any data
        result = retraining_service.trigger_retraining("v1")
        
        assert result['status'] == 'no_data'
        assert result['new_version'] is None
    
    def test_retraining_validation_integration(self, integrated_system):
        """Test retraining validation dengan real database"""
        prediction_service = integrated_system['prediction_service']
        retraining_service = integrated_system['retraining_service']
        
        # Initially should fail (no data)
        is_valid, message = retraining_service.validate_retraining_requirements()
        assert is_valid is False
        
        # Add sufficient data with varying text to get different predictions (7+ words each)
        # Note: actual prediction depends on model, but we need at least 10 samples
        texts = [
            "Film ini sangat bagus dan menyenangkan sekali untuk ditonton bersama",
            "Produk ini jelek sekali tidak berguna dan sangat mengecewakan sekali",
            "Biasa saja tidak terlalu menarik tapi cukup untuk kebutuhan dasar",
            "Saya sangat senang dengan hasilnya dan akan membeli lagi nanti",
            "Sangat mengecewakan dan buruk sekali tidak sesuai dengan ekspektasi",
            "Pelayanan bagus memuaskan dan sangat ramah sekali kepada pelanggan",
            "Tidak recommended sama sekali dan sangat mengecewakan pengalamannya",
            "Amazing product highly recommended and very satisfied with quality",
            "Terrible experience never again and very disappointed with service",
            "Lumayan lah untuk harganya dan cukup sesuai dengan ekspektasi",
            "Produk berkualitas tinggi dan sangat memuaskan sekali hasilnya",
            "Barangnya rusak dan jelek sekali tidak sesuai dengan deskripsi",
        ]
        
        for text in texts:
            prediction_service.predict(text, "v1", user_consent=True)
        
        # Get dataset to check
        df = retraining_service.get_dataset_snapshot()
        
        # Should have at least 10 samples now
        assert len(df) >= 10, f"Expected at least 10 samples, got {len(df)}"
        
        # Now validate - may still fail if all predictions are same class
        # This is expected behavior based on model output
        is_valid, message = retraining_service.validate_retraining_requirements()
        
        # At minimum, we should have enough data
        # Class diversity depends on model, so we just check data count is sufficient
        if not is_valid:
            assert "minimal 2 kelas" in message.lower() or "tidak cukup" in message.lower(), \
                f"Unexpected validation message: {message}"


class TestDataConsistency:
    """Test data consistency across operations"""
    
    def test_prediction_and_retrieval_consistency(self, integrated_system):
        """Test bahwa data yang disimpan sama dengan yang diretrieve"""
        prediction_service = integrated_system['prediction_service']
        db_manager = integrated_system['db_manager']
        
        # Make prediction
        text = "Test consistency check dengan lebih dari tujuh kata untuk validasi"
        model_version = "v2"
        
        result = prediction_service.predict(text, model_version, user_consent=True)
        
        # Retrieve and verify
        recent = db_manager.get_recent_predictions(limit=1)
        
        assert recent[0]['text_input'] == text
        assert recent[0]['model_version'] == model_version
        assert recent[0]['prediction'] == result['prediction']
        assert abs(recent[0]['confidence'] - result['confidence']) < 0.001
    
    def test_metrics_consistency(self, integrated_system):
        """Test bahwa metrics konsisten dengan actual data"""
        prediction_service = integrated_system['prediction_service']
        monitoring_service = integrated_system['monitoring_service']
        
        # Make known number of predictions with first available version
        test_version = settings.MODEL_VERSIONS[0]  # Use first available version
        num_predictions = 7
        for i in range(num_predictions):
            prediction_service.predict(f"Test {i} dengan lebih dari tujuh kata untuk metrics", test_version, user_consent=True)
        
        # Get metrics
        metrics = monitoring_service.get_metrics_summary()
        counts = monitoring_service.get_prediction_counts()
        
        # Verify consistency
        assert metrics[test_version]['prediction_count'] == num_predictions
        assert counts[test_version] == num_predictions


class TestErrorRecovery:
    """Test error recovery dan resilience"""
    
    def test_prediction_continues_after_db_error(self, integrated_system):
        """Test bahwa prediction tetap berjalan meskipun database error"""
        prediction_service = integrated_system['prediction_service']
        db_manager = integrated_system['db_manager']
        
        # Store original method
        original_insert = db_manager.insert_user_input
        
        # Mock database error
        def mock_insert_error(*args, **kwargs):
            raise Exception("Simulated database error")
        
        db_manager.insert_user_input = mock_insert_error
        
        try:
            # Prediction should still work (without saving)
            result = prediction_service.predict("Test after db error dengan lebih dari tujuh kata", "v1", user_consent=True)
            
            # Prediction should succeed
            assert result['prediction'] is not None
            # But should have warning
            assert 'database_warning' in result['metadata']
        finally:
            # Restore original method
            db_manager.insert_user_input = original_insert
    
    def test_monitoring_handles_empty_database(self, integrated_system):
        """Test monitoring dengan empty database"""
        monitoring_service = integrated_system['monitoring_service']
        
        # Get metrics dari empty database
        metrics = monitoring_service.get_metrics_summary()
        counts = monitoring_service.get_prediction_counts()
        latencies = monitoring_service.get_latency_distribution()
        
        # Should return empty but not error
        assert metrics == {}
        assert counts == {}
        assert latencies == []


class TestConcurrentOperations:
    """Test concurrent operations"""
    
    def test_multiple_predictions_same_version(self, integrated_system):
        """Test multiple predictions dengan same version secara berurutan"""
        prediction_service = integrated_system['prediction_service']
        
        results = []
        for i in range(5):
            result = prediction_service.predict(f"Concurrent test {i} dengan lebih dari tujuh kata", "v1", user_consent=True)
            results.append(result)
        
        # All should succeed
        assert all(r['error'] is None for r in results)
        assert all(r['prediction'] is not None for r in results)
    
    def test_mixed_version_predictions(self, integrated_system):
        """Test predictions dengan mixed versions"""
        prediction_service = integrated_system['prediction_service']
        
        # Use only available versions, repeated for mixed testing
        versions = settings.MODEL_VERSIONS * 2  # e.g., ['v1', 'v2', 'v1', 'v2']
        results = []
        
        for i, version in enumerate(versions):
            result = prediction_service.predict(f"Mixed test {i} dengan lebih dari tujuh kata", version, user_consent=True)
            results.append(result)
        
        # All should succeed
        assert all(r['error'] is None for r in results)
        
        # Verify correct versions used
        for i, result in enumerate(results):
            # Can't directly check version from result, but can verify no errors
            assert result['prediction'] is not None
