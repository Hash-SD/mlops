"""
Main Streamlit application untuk Sistem AI Berbasis Teks.
Entry point untuk aplikasi MLOps dengan redesign modern (Single Column Layout).
"""

import streamlit as st
import logging
from config.settings import settings
from utils.logger import setup_logger

# Import database & services
from database.db_manager import DatabaseManager
from database.db_manager_supabase import SupabaseDatabaseManager
from models.model_loader import ModelLoader
from services.prediction_service import PredictionService
from services.monitoring_service import MonitoringService
from services.retraining_service import RetrainingService

# Import New UI Components
from ui.sidebar import render_sidebar
from ui.main_area import render_main_layout, render_empty_state, render_result_section, render_example_buttons
from ui.monitoring import render_monitoring_dashboard
from ui.model_management import render_model_management_page
from ui.styles import load_css

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
    """
    Initialize DB and Model Loader. Cached resource.
    Returns: (db_manager, model_loader) tuple
    """
    # 1. Database
    try:
        if settings.is_supabase():
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                raise ValueError("Missing Supabase credentials")
            db_manager = SupabaseDatabaseManager(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            if not db_manager.connect(): raise Exception("Failed to connect to Supabase")
        else:
            db_manager = DatabaseManager(settings.get_database_path())
            db_manager.connect()
            db_manager.initialize_schema()
    except Exception as e:
        logger.error(f"DB Init failed: {e}")
        # Fallback
        db_manager = DatabaseManager("mlops_app.db")
        db_manager.connect()
        db_manager.initialize_schema()
        
    # 2. Model Loader
    try:
        model_loader = ModelLoader(mlflow_tracking_uri=settings.MLFLOW_TRACKING_URI)
    except:
        model_loader = ModelLoader(mlflow_tracking_uri=None)
        
    return db_manager, model_loader

def main():
    # 1. Page Config
    st.set_page_config(
        page_title=settings.APP_TITLE,
        page_icon=settings.APP_ICON,
        layout="wide", # We restrict width via CSS, but keep wide for background
        initial_sidebar_state="expanded"
    )
    
    # 2. Load Custom CSS
    load_css()
    
    # 3. Initialization
    initialize_session_state()
    
    with st.spinner("🚀 Memuat sistem..."):
        db_manager, model_loader = initialize_resources()
        
    # Initialize Services
    prediction_service = PredictionService(db_manager, model_loader)
    monitoring_service = MonitoringService(db_manager)
    retraining_service = RetrainingService(db_manager, settings.MLFLOW_TRACKING_URI)
    
    # 4. Render Sidebar
    selected_page = render_sidebar(retraining_service)
    
    # 5. Page Routing
    if selected_page == "Dashboard" or selected_page == "🔮 Prediksi":
        # --- NEW MAIN LAYOUT ---
        
        # A. Render Header & Input & Action
        text_input, analyze_clicked = render_main_layout()
        
        # B. Handle Prediction Logic
        if analyze_clicked and text_input:
            with st.spinner("🤖 Menganalisis sentimen..."):
                try:
                    result = prediction_service.predict(
                        text=text_input,
                        model_version=st.session_state.selected_model_version,
                        user_consent=st.session_state.user_consent
                    )
                    st.session_state.current_prediction = result
                    
                    # Add to local history (optional, currently not displayed prominently in new design)
                    if 'prediction_history' not in st.session_state: 
                        st.session_state.prediction_history = []
                    st.session_state.prediction_history.insert(0, result)
                    
                except Exception as e:
                    st.error(f"Error: {e}")
                    logger.error(f"Prediction error: {e}")
        
        # C. Render Output: Either Result OR Nothing (Empty State Removed)
        if st.session_state.current_prediction:
            render_result_section(st.session_state.current_prediction)
        # Else: Do nothing (Clean interface as requested)
            
        # D. Examples (Always at bottom for engagement)
        st.markdown("---")
        render_example_buttons()


        # E. History Section (Restored)
        st.markdown("---")
        st.markdown("### 📜 Riwayat Prediksi Terakhir")
        
        try:
             # Fetch recent history
             history = db_manager.get_recent_predictions(limit=5)
             if history:
                 # Start building HTML string
                 full_html = '<div class="glass-card">'
                 
                 full_html += """
                 <table class="glass-table">
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
                     # Truncate long text
                     if len(text) > 50: text = text[:50] + "..."
                     
                     pred = h.get('prediction', '').lower()
                     conf = h.get('confidence', 0)  # Fixed: changed from 'confidence_score' to 'confidence'
                     
                     # Badge class
                     badge_class = "badge-neu"
                     if "posit" in pred: badge_class = "badge-pos"
                     elif "negat" in pred: badge_class = "badge-neg"
                     
                     full_html += f"""<tr>
<td>{time_str}</td>
<td style="font-style: italic;">"{text}"</td>
<td><span class="{badge_class}">{pred.capitalize()}</span></td>
<td>{conf:.1%}</td>
</tr>"""
                     
                 full_html += "</tbody></table></div>"
                 st.markdown(full_html, unsafe_allow_html=True)
                 
             else:
                 st.info("Belum ada riwayat prediksi.")
        except Exception as e:
             st.error(f"Gagal memuat riwayat: {e}")

    elif selected_page == "Monitoring" or selected_page == "📊 Monitoring":
        st.title("📊 Monitoring Dashboard")
        render_monitoring_dashboard(monitoring_service)
        
    elif selected_page == "Management" or selected_page == "🚀 Model Management":
        # Title handled inside render_model_management_page for custom styling
        render_model_management_page()

    # Footer
    st.markdown(
        """
        <div class="footer">
            Powered by TextAI Engine <br>
            Made with ❤️ by Tim Pengembang | © 2025
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
