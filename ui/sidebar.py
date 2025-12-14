"""Sidebar components with modern styling."""

import streamlit as st
from config.settings import settings

# Model Metadata
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
    """Render modern sidebar with separated sections."""
    with st.sidebar:
        # Header & Branding
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 30px;">
                <div class="sidebar-logo-icon">🔎</div>
                <h1 style="font-size: 2.8rem !important; margin: 0; font-weight: 800; letter-spacing: -2px; line-height: 1.2; color: #1E293B;">
                    insightext
                </h1>
                <span class="sidebar-subtitle">Sentiment Analysis</span>
            </div>
            <hr style="border: none; height: 1px; background: linear-gradient(90deg, transparent, #E2E8F0, transparent); margin: 20px 0;">
            """, 
            unsafe_allow_html=True
        )
        
        # User Mode Selection
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
            st.markdown('<p class="mode-caption">Mode sederhana untuk analisis cepat.</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="mode-caption">Mode detail dengan metrik performa lengkap.</p>', unsafe_allow_html=True)
            
        st.divider()

        # Main Navigation
        st.markdown("### 🧭 Navigation")
        selected_page = st.radio(
            "Go to",
            options=["Prediksi", "Monitoring", "Model Management"],
            label_visibility="collapsed"
        )
        
        st.divider()

        # Configuration Section
        with st.expander("⚙️  Pengaturan & Model", expanded=True):
            st.markdown('<p class="section-label"><strong>Model Version</strong></p>', unsafe_allow_html=True)
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
            
            if mode == "Expert":
                meta = MODEL_METADATA.get(selected_v, {})
                st.info(f"{meta.get('model_type')}\nAcc: {meta.get('accuracy'):.1%}")

            st.markdown('<p class="section-label"><strong>Data Privacy</strong></p>', unsafe_allow_html=True)
            dont_save = st.checkbox(
                "Don't save my data",
                value=st.session_state.get('dont_save_data', False)
            )
            st.session_state['dont_save_data'] = dont_save
            st.session_state['user_consent'] = not dont_save

        st.divider()

        # Team Section
        st.markdown("### 👥 Tim Pengembang")
        team_members = [
            "Hermawan Manurung",
            "Najla Juwairia",
            "Presilia",
            "Dea Mutia Risani",
            "Pardi Octaviando"
        ]
        
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
