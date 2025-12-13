"""
Sidebar components restored to original navigation logic but with modern styling.
Includes Team Section as requested.
"""

import streamlit as st
from config.settings import settings

# Model Metadata definitions
MODEL_METADATA = {
    'v1': {
        'name': 'NB Indonesian Sentiment',
        'model_type': 'MultinomialNB + TF-IDF',
        'task': 'Sentiment Analysis',
        'language': 'Indonesian',
        'labels': ['negatif', 'netral', 'positif'],
        'accuracy': 0.6972,
        'description': 'Analisis sentimen Bahasa Indonesia (3 kelas)'
    },
    'v2': {
        'name': 'NB English Sentiment',
        'model_type': 'MultinomialNB + TF-IDF',
        'task': 'Sentiment Analysis',
        'language': 'English',
        'labels': ['negative', 'positive'],
        'accuracy': 0.8647,
        'description': 'Analisis sentimen English (binary)'
    }
}

def render_sidebar(retraining_service=None) -> str:
    """
    Render modern sidebar with separated sections.
    """
    with st.sidebar:
        # 1. Header & Branding
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 30px;">
                <div style="font-size: 8rem !important; line-height: 1 !important; margin-bottom: 15px; display: block;">🔎</div>
                <h1 style="font-size: 3.5rem !important; margin: 0; font-weight: 800; letter-spacing: -2px; line-height: 1.2; color: #1E293B;">
                    insightext
                </h1>
                <p style="color: #64748B; margin-top: 10px; font-size: 1.2rem !important;">
                    Enterprise Sentiment Analysis
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # 2. User Mode Selection
        st.markdown("### 👤 User Mode")
        mode = st.radio(
            "Select Interface Mode",
            options=["Beginner", "Expert"],
            index=0 if st.session_state.get('user_mode', 'Beginner') == 'Beginner' else 1,
            label_visibility="collapsed",
            key="user_mode_radio",
            horizontal=True
        )
        st.session_state['user_mode'] = mode
        
        if mode == "Beginner":
            st.caption("Mode sederhana untuk analisis cepat.")
        else:
            st.caption("Mode detail dengan metrik performa lengkap.")
            
        st.divider()

        # 3. Main Navigation (Restored)
        st.markdown("### 🧭 Navigation")
        selected_page = st.radio(
            "Go to",
            options=["🔮 Prediksi", "📊 Monitoring", "🚀 Model Management"],
            label_visibility="collapsed"
        )
        
        st.divider()

        # 4. Configuration Section
        with st.expander("⚙️  Pengaturan & Model", expanded=True):
            # Model Version
            st.markdown("**Model Version**")
            model_options = {'v1': '🇮🇩 Indonesian', 'v2': '🇺🇸 English'}
            current_version = st.session_state.get('selected_model_version', 'v1')
            
            selected_v = st.selectbox(
                "Model",
                options=list(model_options.keys()),
                format_func=lambda x: model_options[x],
                index=list(model_options.keys()).index(current_version),
                label_visibility="collapsed"
            )
            st.session_state['selected_model_version'] = selected_v
            
            # Show small model info
            if mode == "Expert":
                meta = MODEL_METADATA.get(selected_v, {})
                st.info(f"{meta.get('model_type')}\nAcc: {meta.get('accuracy'):.1%}")

            # Data Consent
            st.markdown("**Data Privacy**")
            dont_save = st.checkbox(
                "Don't save my data",
                value=st.session_state.get('dont_save_data', False)
            )
            st.session_state['dont_save_data'] = dont_save
            st.session_state['user_consent'] = not dont_save

        st.divider()

        # 5. Tim Pengembang (New List)
        st.markdown("### 👥 Tim Pengembang")
        team_members = [
            "Hermawan Manurung",
            "Pardi Octaviando",
            "Najla Juwairia",
            "Dea Mutia Risani",
            "Presilia"
        ]
        
        # Build HTML string first
        team_html = '<div style="background-color: #F8FAFC; padding: 15px; border-radius: 8px; border: 1px solid #E2E8F0;">'
        for member in team_members:
             team_html += f"<div style='margin-bottom: 5px; color: #475569; font-weight: 500;'>• {member}</div>"
        team_html += '</div>'
        
        st.markdown(team_html, unsafe_allow_html=True)

        # Footer
        st.markdown(
            """
            <div style="margin-top: 30px; font-size: 0.8rem; color: #9aa0a6; text-align: center;">
                Made by Kelompok 6-RA
            </div>
            """,
            unsafe_allow_html=True
        )
        
    return selected_page
