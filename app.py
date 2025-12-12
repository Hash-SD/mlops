"""
Main Streamlit application untuk Sistem AI Berbasis Teks.
Entry point untuk aplikasi MLOps dengan model versioning dan monitoring.
"""

import streamlit as st
import logging
from pathlib import Path

# Import configuration
from config.settings import settings

# Import utilities
from utils.logger import setup_logger, log_error

# Import database
from database.db_manager import DatabaseManager
from database.db_manager_supabase import SupabaseDatabaseManager

# Import models
from models.model_loader import ModelLoader

# Import services
from services.prediction_service import PredictionService
from services.monitoring_service import MonitoringService
from services.retraining_service import RetrainingService

# Import UI components
from ui.sidebar import render_sidebar
from ui.main_area import render_main_area, render_prediction_history, render_results, render_prediction_button
from ui.monitoring import render_monitoring_dashboard


# Setup logger
logger = setup_logger(
    name='mlops_app',
    log_file=settings.LOG_FILE,
    level=getattr(logging, settings.LOG_LEVEL.upper())
)


def initialize_session_state():
    """
    Initialize Streamlit session state dengan default values.
    Check if session state keys exist sebelum initialize untuk avoid overwriting.
    """
    # Model selection
    if 'selected_model_version' not in st.session_state:
        st.session_state.selected_model_version = settings.DEFAULT_MODEL_VERSION
        logger.debug(f"Initialized selected_model_version: {settings.DEFAULT_MODEL_VERSION}")
    
    # User consent (default True - otomatis simpan)
    if 'user_consent' not in st.session_state:
        st.session_state.user_consent = True
        logger.debug("Initialized user_consent: True (auto-save enabled)")
    
    # Dont save data flag
    if 'dont_save_data' not in st.session_state:
        st.session_state.dont_save_data = False
        logger.debug("Initialized dont_save_data: False")
    
    # Prediction history
    if 'prediction_history' not in st.session_state:
        st.session_state.prediction_history = []
        logger.debug("Initialized prediction_history: []")
    
    # Current prediction result
    if 'current_prediction' not in st.session_state:
        st.session_state.current_prediction = None
        logger.debug("Initialized current_prediction: None")
    
    # Retraining status
    if 'retraining_status' not in st.session_state:
        st.session_state.retraining_status = 'idle'
        logger.debug("Initialized retraining_status: idle")
    
    # Text input
    if 'text_input' not in st.session_state:
        st.session_state.text_input = ""
        logger.debug("Initialized text_input: empty")


@st.cache_data(ttl=60)  # Cache for 60 seconds
def get_recent_predictions_cached(_db_manager, limit: int = 10):
    """
    Get recent predictions with caching.
    Cache expires after 60 seconds untuk balance freshness dan performance.
    
    Args:
        _db_manager: DatabaseManager or SupabaseDatabaseManager instance (underscore prefix to skip hashing)
        limit: Number of predictions to fetch
        
    Returns:
        List of recent prediction records
    """
    try:
        return _db_manager.get_recent_predictions(limit=limit)
    except Exception as e:
        logger.error(f"Error fetching cached predictions: {e}")
        return []


@st.cache_resource
def get_model_loader() -> ModelLoader:
    """
    Get cached model loader instance.
    Cached as resource untuk reuse model loader across reruns.
    
    Returns:
        ModelLoader: Cached model loader instance
    """
    try:
        model_loader = ModelLoader(mlflow_tracking_uri=settings.MLFLOW_TRACKING_URI)
        logger.info("Model loader created and cached")
        return model_loader
    except Exception as e:
        logger.error(f"Failed to create model loader: {e}")
        # Try fallback without MLflow
        model_loader = ModelLoader(mlflow_tracking_uri=None)
        logger.info("Fallback model loader created and cached")
        return model_loader


@st.cache_resource
def initialize_database():
    """
    Initialize database connection dan create tables jika belum ada.
    Cached as resource untuk reuse connection across reruns.
    Supports: SQLite, PostgreSQL, and Supabase (REST API).
    Falls back to SQLite if cloud connection fails.
    
    Returns:
        DatabaseManager or SupabaseDatabaseManager: Initialized database manager instance
        
    Raises:
        Exception: Jika database initialization gagal
    """
    try:
        # Check if using Supabase REST API
        if settings.is_supabase():
            logger.info("Using Supabase REST API...")
            
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set when DATABASE_TYPE=supabase")
            
            db_manager = SupabaseDatabaseManager(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_KEY
            )
            
            # Test connection
            if db_manager.connect():
                logger.info("Supabase REST API connection established")
                return db_manager
            else:
                raise Exception("Failed to connect to Supabase REST API")
        
        # Use traditional DatabaseManager for SQLite/PostgreSQL
        db_path = settings.get_database_path()
        logger.info(f"Initializing database: {db_path}")
        
        # Create database manager
        db_manager = DatabaseManager(db_url=db_path)
        
        # Connect to database
        db_manager.connect()
        
        # Initialize schema if tables don't exist
        schema_initialized = db_manager.initialize_schema()
        
        if schema_initialized:
            logger.info("Database initialized successfully")
        else:
            logger.warning("Database initialization returned False, but continuing")
        
        return db_manager
        
    except Exception as e:
        # If Supabase or PostgreSQL fails, fallback to SQLite
        if settings.is_supabase() or settings.is_postgresql():
            logger.warning(f"Cloud database connection failed: {e}")
            logger.info("Falling back to local SQLite database...")
            
            try:
                fallback_db = "mlops_app.db"
                db_manager = DatabaseManager(db_url=fallback_db)
                db_manager.connect()
                db_manager.initialize_schema()
                logger.info(f"Successfully connected to fallback SQLite: {fallback_db}")
                st.warning("⚠️ Menggunakan database lokal (SQLite) karena koneksi ke cloud database gagal.")
                return db_manager
            except Exception as fallback_error:
                error_msg = f"Fallback ke SQLite juga gagal: {str(fallback_error)}"
                logger.error(error_msg)
                raise Exception(error_msg)
        else:
            error_msg = f"Gagal menginisialisasi database: {str(e)}"
            logger.error(error_msg)
            log_error(logger, e, {'database_url': settings.DATABASE_URL})
            raise Exception(error_msg)


def main():
    """
    Main application entry point.
    Configure Streamlit, setup logging, initialize database, dan render UI.
    """
    # Configure Streamlit page
    st.set_page_config(
        page_title=settings.APP_TITLE,
        page_icon=settings.APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    logger.info("=" * 80)
    logger.info("Application started")
    logger.info(f"App Title: {settings.APP_TITLE}")
    logger.info(f"Database: {settings.DATABASE_URL}")
    logger.info(f"MLflow URI: {settings.MLFLOW_TRACKING_URI}")
    logger.info("=" * 80)
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize database with loading indicator
    try:
        with st.spinner("⏳ Menginisialisasi database..."):
            db_manager = initialize_database()
        st.toast("✅ Database siap", icon="✅")
    except Exception as e:
        st.error(f"❌ Gagal menginisialisasi database: {str(e)}")
        st.error("Silakan periksa konfigurasi database dan coba lagi.")
        st.info("💡 **Saran Troubleshooting:**\n"
                "- Pastikan file database dapat diakses\n"
                "- Periksa izin akses folder database\n"
                "- Verifikasi konfigurasi DATABASE_URL di file .env")
        logger.error("Application stopped due to database initialization failure")
        st.stop()
    
    # Initialize model loader (cached)
    try:
        model_loader = get_model_loader()
        logger.info("Model loader initialized")
    except Exception as e:
        st.error(f"❌ Gagal menginisialisasi model loader: {str(e)}")
        st.warning("⚠️ Aplikasi akan menggunakan model default")
        logger.error(f"Model loader initialization failed: {e}")
        log_error(logger, e, {'mlflow_uri': settings.MLFLOW_TRACKING_URI})
        # Don't stop, use fallback
        try:
            model_loader = ModelLoader(mlflow_tracking_uri=None)
            logger.info("Fallback model loader initialized")
        except Exception as fallback_error:
            st.error(f"❌ Gagal menginisialisasi fallback model loader: {str(fallback_error)}")
            logger.error(f"Fallback model loader failed: {fallback_error}")
            st.stop()
    
    # Initialize services
    try:
        prediction_service = PredictionService(
            db_manager=db_manager,
            model_loader=model_loader
        )
        monitoring_service = MonitoringService(db_manager=db_manager)
        retraining_service = RetrainingService(
            db_manager=db_manager,
            mlflow_tracking_uri=settings.MLFLOW_TRACKING_URI
        )
        logger.info("All services initialized successfully")
    except Exception as e:
        st.error(f"❌ Gagal menginisialisasi services: {str(e)}")
        st.error("Aplikasi tidak dapat dilanjutkan. Silakan hubungi administrator.")
        logger.error(f"Services initialization failed: {e}")
        log_error(logger, e)
        st.stop()
    
    # Render sidebar and get selected page
    selected_page = render_sidebar(retraining_service=retraining_service)
    
    # Page: Prediksi
    if selected_page == "🔮 Prediksi":
        st.title("🔮 Prediksi")
        st.markdown("---")
        
        # Render main area (input)
        text_input = render_main_area()
        
        # Render prediction button and handle click
        button_clicked = render_prediction_button()
        
        # Handle prediction button click
        if button_clicked:
            # Get selected model version and consent from session state
            model_version = st.session_state.selected_model_version
            user_consent = st.session_state.user_consent
            
            # Validate input
            from utils.validators import validate_text_input
            is_valid, error_message = validate_text_input(text_input)
            
            if not is_valid:
                st.error(f"❌ {error_message}")
                logger.warning(f"Invalid input: {error_message}")
            else:
                # Show spinner while processing
                with st.spinner("⏳ Memproses prediksi..."):
                    try:
                        # Call prediction service
                        result = prediction_service.predict(
                            text=text_input,
                            model_version=model_version,
                            user_consent=user_consent
                        )
                        
                        # Check if prediction has error
                        if result.get('error'):
                            st.error(f"❌ {result['error']}")
                            logger.warning(f"Prediction returned error: {result['error']}")
                        else:
                            # Store result in session state
                            st.session_state.current_prediction = result
                            
                            # Add to prediction history
                            if 'prediction_history' not in st.session_state:
                                st.session_state.prediction_history = []
                            st.session_state.prediction_history.insert(0, result)
                            
                            # Show success toast notification
                            st.toast("✅ Prediksi berhasil!", icon="✅")
                            
                            logger.info(
                                f"Prediction completed: model={model_version}, "
                                f"confidence={result['confidence']:.2f}, "
                                f"latency={result['latency']:.3f}s"
                            )
                        
                    except ValueError as e:
                        st.error(f"❌ Input tidak valid: {str(e)}")
                        logger.error(f"Validation error: {e}")
                        log_error(logger, e, {
                            'model_version': model_version,
                            'text_length': len(text_input),
                            'user_consent': user_consent
                        })
                    except ConnectionError as e:
                        st.error(f"❌ Gagal terhubung ke database: {str(e)}")
                        st.warning("⚠️ Prediksi berhasil, tetapi tidak dapat menyimpan ke database")
                        logger.error(f"Database connection error: {e}")
                        log_error(logger, e, {
                            'model_version': model_version,
                            'text_length': len(text_input),
                            'user_consent': user_consent
                        })
                    except Exception as e:
                        st.error(f"❌ Terjadi kesalahan saat memproses prediksi: {str(e)}")
                        st.info("💡 Silakan coba lagi atau hubungi administrator jika masalah berlanjut")
                        logger.error(f"Prediction failed: {e}")
                        log_error(logger, e, {
                            'model_version': model_version,
                            'text_length': len(text_input),
                            'user_consent': user_consent
                        })
        
        # Display results if available
        if st.session_state.current_prediction:
            render_results(st.session_state.current_prediction)
        
        # Display prediction history (tanpa caching untuk menghindari issue hash)
        st.markdown("---")
        st.subheader("📜 Riwayat Prediksi")
        try:
            history_data = db_manager.get_recent_predictions(limit=settings.PREDICTION_HISTORY_LIMIT)
            render_prediction_history(history_data=history_data)
        except Exception as e:
            st.error(f"❌ Gagal memuat riwayat prediksi: {str(e)}")
            logger.error(f"Error loading prediction history: {e}")
            log_error(logger, e)
    
    # Page: Monitoring
    elif selected_page == "📊 Monitoring":
        st.title("📊 Monitoring & Manajemen Model")
        st.caption("Pantau performa model dan kelola deployment secara real-time")
        st.markdown("---")
        try:
            render_monitoring_dashboard(monitoring_service=monitoring_service)
        except Exception as e:
            st.error(f"❌ Gagal memuat dashboard monitoring: {str(e)}")
            logger.error(f"Error rendering monitoring dashboard: {e}")
            log_error(logger, e)


if __name__ == "__main__":
    main()
