"""
Main Streamlit application for Text AI System.
Entry point for MLOps application with modern single column layout.
"""

import streamlit as st
import logging

from config.settings import settings
from utils.logger import setup_logger
from database import DatabaseManager, SupabaseDatabaseManager
from models import ModelLoader
from services import PredictionService, MonitoringService, RetrainingService
from ui import (
    load_css,
    render_sidebar,
    render_main_layout,
    render_result_section,
    render_example_buttons,
    render_monitoring_dashboard,
    render_model_management_page
)

# Setup logger
logger = setup_logger(
    name='mlops_app',
    log_file=settings.LOG_FILE,
    level=getattr(logging, settings.LOG_LEVEL.upper())
)


def initialize_session_state():
    """Initialize session state defaults."""
    defaults = {
        'selected_model_version': settings.DEFAULT_MODEL_VERSION,
        'user_consent': True,
        'dont_save_data': False,
        'prediction_history': [],
        'current_prediction': None,
        'text_input_area': "",
        'user_mode': 'Beginner'
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource
def initialize_resources():
    """Initialize DB and Model Loader (cached resource)."""
    # Database initialization
    try:
        if settings.is_supabase():
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                raise ValueError("Missing Supabase credentials")
            db_manager = SupabaseDatabaseManager(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            if not db_manager.connect():
                raise Exception("Failed to connect to Supabase")
        else:
            db_manager = DatabaseManager(settings.get_database_path())
            db_manager.connect()
            db_manager.initialize_schema()
    except Exception as e:
        logger.error(f"DB Init failed: {e}")
        # Fallback to SQLite
        db_manager = DatabaseManager("mlops_app.db")
        db_manager.connect()
        db_manager.initialize_schema()
    
    # Model Loader initialization
    try:
        model_loader = ModelLoader(mlflow_tracking_uri=settings.MLFLOW_TRACKING_URI)
    except Exception:
        model_loader = ModelLoader(mlflow_tracking_uri=None)
    
    return db_manager, model_loader


def render_prediction_history(db_manager):
    """Render prediction history section."""
    st.markdown("---")
    st.markdown("### 📜 Riwayat Prediksi Terakhir")
    
    try:
        history = db_manager.get_recent_predictions(limit=5)
        if not history:
            st.info("Belum ada riwayat prediksi.")
            return
        
        html = '<div class="glass-card"><table class="glass-table">'
        html += """
        <thead>
            <tr>
                <th style="width: 20%;">Waktu</th>
                <th style="width: 45%;">Teks</th>
                <th style="width: 20%;">Prediksi</th>
                <th style="width: 15%;">Confidence</th>
            </tr>
        </thead>
        <tbody>
        """
        
        for h in history:
            time_str = h.get('timestamp', '')[:16].replace('T', ' ')
            text = h.get('text_input', '')
            if len(text) > 50:
                text = text[:50] + "..."
            
            pred = h.get('prediction', '').lower()
            conf = h.get('confidence', 0)
            
            badge_class = "badge-neu"
            if "posit" in pred:
                badge_class = "badge-pos"
            elif "negat" in pred:
                badge_class = "badge-neg"
            
            html += f"""<tr>
                <td>{time_str}</td>
                <td style="font-style: italic;">"{text}"</td>
                <td><span class="{badge_class}">{pred.capitalize()}</span></td>
                <td>{conf:.1%}</td>
            </tr>"""
        
        html += "</tbody></table></div>"
        st.markdown(html, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Gagal memuat riwayat: {e}")


def render_footer():
    """Render footer."""
    st.markdown(
        """
        <div class="footer">
            Made with ❤️ by Tim Pengembang | © 2025
        </div>
        """,
        unsafe_allow_html=True
    )


def main():
    # Page Config
    st.set_page_config(
        page_title=settings.APP_TITLE,
        page_icon=settings.APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load CSS
    load_css()
    
    # Initialize
    initialize_session_state()
    
    with st.spinner("🚀 Memuat sistem..."):
        db_manager, model_loader = initialize_resources()
    
    # Initialize Services
    prediction_service = PredictionService(db_manager, model_loader)
    monitoring_service = MonitoringService(db_manager)
    retraining_service = RetrainingService(db_manager, settings.MLFLOW_TRACKING_URI)
    
    # Render Sidebar
    selected_page = render_sidebar(retraining_service)
    
    # Page Routing
    if selected_page in ["Dashboard", "Prediksi"]:
        # Main Prediction Page
        text_input, analyze_clicked = render_main_layout()
        
        # Handle Prediction
        if analyze_clicked and text_input:
            with st.spinner("🤖 Menganalisis sentimen..."):
                try:
                    result = prediction_service.predict(
                        text=text_input,
                        model_version=st.session_state.selected_model_version,
                        user_consent=st.session_state.user_consent
                    )
                    st.session_state.current_prediction = result
                    
                    if 'prediction_history' not in st.session_state:
                        st.session_state.prediction_history = []
                    st.session_state.prediction_history.insert(0, result)
                    
                except Exception as e:
                    st.error(f"Error: {e}")
                    logger.error(f"Prediction error: {e}")
        
        # Render Result
        if st.session_state.current_prediction:
            render_result_section(st.session_state.current_prediction, db_manager)
        
        # Examples
        st.markdown("---")
        render_example_buttons()
        
        # History
        render_prediction_history(db_manager)
    
    elif selected_page in ["Monitoring"]:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 25px;">
                <h1 style="font-size: 1.8rem; margin-bottom: 8px;">📊 Monitoring Dashboard</h1>
                <p style="color: #64748B; font-size: 0.9rem;">Pantau performa dan metrik model secara real-time</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        render_monitoring_dashboard(monitoring_service)
    
    elif selected_page in ["Management", "Model Management"]:
        render_model_management_page(db_manager)
    
    # Footer
    render_footer()


if __name__ == "__main__":
    main()
