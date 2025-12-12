"""
Main area components refactored for new Single Column Vertical Layout.
Matches 'CogniDesk' reference: Title -> Input -> Empty State/Result -> Examples.
"""

import streamlit as st
from config.settings import settings
from typing import Dict, Any

def render_main_layout() -> str:
    """
    Renders the entire main content area.
    Returns:
        str: The text input to be analyzed (if Action triggered)
    """
    # 1. Header with Icon
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="font-size: 1.8rem; margin-bottom: 5px;">✨ Identifikasi Sentimen</h1>
            <p style="color: #64748B; font-size: 0.9rem; margin-top: 0;">Analisis emosi dan sentimen dari teks ulasan pelanggan secara instan.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. Input Section
    st.markdown("### 📝 Input Teks")
    
    # Handle Examples State
    if 'text_input_area' not in st.session_state:
        st.session_state.text_input_area = ""

    # Text Area
    text_input = st.text_area(
        "Input Text",
        value=st.session_state.text_input_area,
        height=150,
        placeholder="Ketik ulasan di sini atau pilih contoh di bawah...",
        label_visibility="collapsed"
    )
    
    # Character Counter (Subtle)
    if text_input:
        st.caption(f"{len(text_input)}/{settings.MAX_INPUT_LENGTH} karakter")
    
    # Action Button
    col_btn, _ = st.columns([1, 2]) # Limit button width slightly? No, full width is better in mobile, let's stick to simple.
    analyze_clicked = st.button("🔍 Analisis Sekarang", type="primary", use_container_width=True, disabled=not text_input)
    
    return text_input, analyze_clicked

def render_empty_state():
    """Renders the dotted empty state box."""
    st.markdown(
        """
        <div class="empty-state-box">
            <div style="font-size: 3rem; opacity: 0.5;">📁</div>
            <h3 style="margin: 10px 0 0 0; color: #475569;">Belum ada teks dipilih</h3>
            <p style="font-size: 0.9rem; margin: 0;">Silakan ketik teks di atas atau gunakan contoh di bawah untuk memulai analisis.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_example_buttons():
    """Renders the 'Coba Contoh Gambar' (Text equivalent) section."""
    st.markdown("### 🧪 Coba Contoh Teks")
    st.caption("Tidak punya teks? Klik salah satu tombol di bawah untuk mencoba demo:")
    
    # Get selected model version
    selected_model = st.session_state.get('selected_model_version', 'v1')
    
    # Example Data - language specific
    if selected_model == 'v2':  # English model
        examples = [
            ("👍 Positive", "This product is amazing! It has greatly improved my daily workflow.", "v2"),
            ("👎 Negative", "Very disappointing, the app crashes frequently and runs slowly.", "v2"),
        ]
    else:  # v1 - Indonesian model
        examples = [
            ("👍 Positif", "Luar biasa! Produk ini sangat membantu pekerjaan saya sehari-hari.", "v1"),
            ("👎 Negatif", "Sangat mengecewakan, aplikasi sering crash dan lambat.", "v1"),
            ("😐 Netral", "Pengiriman standar, barang sampai sesuai estimasi waktu.", "v1")
        ]
    
    # Custom Grid for Buttons
    cols = st.columns(len(examples))
    for i, (label, text, ver) in enumerate(examples):
        # We use a callback to set state
        if cols[i].button(label, key=f"ex_btn_{i}", use_container_width=True):
            st.session_state.text_input_area = text
            st.rerun() # Force reload to populate text area

def render_result_section(prediction_result: Dict[str, Any]):
    """
    Render results in a clean glass card.
    """
    if not prediction_result:
        return

    pred_label = prediction_result.get('prediction', 'Unknown')
    confidence = prediction_result.get('confidence', 0.0)
    
    # Colors
    color_map = {
        'positif': ('#10B981', '😊'), # Green
        'positive': ('#10B981', '😊'),
        'negatif': ('#EF4444', '😠'), # Red
        'negative': ('#EF4444', '😠'),
        'netral': ('#F59E0B', '😐')   # Amber
    }
    
    color, icon = color_map.get(pred_label.lower(), ('#64748B', '❓'))
    
    st.markdown(
        f"""<div class="glass-card" style="border-left: 5px solid {color}; margin-top: 20px;">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div style="flex: 1; min-width: 0;">
                    <p style="color: #64748B; margin-bottom: 5px; font-size: 0.8rem;">Hasil Analisis</p>
                    <h2 style="color: {color}; margin: 0; display: flex; align-items: center; gap: 8px; font-size: 1.2rem; word-break: keep-all;">
                        <span style="font-size: 1.2rem;">{icon}</span> {pred_label.upper()}
                    </h2>
                </div>
                <div style="text-align: right; flex-shrink: 0;">
                    <p style="font-size: 1.5rem; font-weight: 700; color: #1E293B; margin: 0;">{confidence:.0%}</p>
                    <p style="color: #64748B; margin: 0; font-size: 0.75rem;">Confidence</p>
                </div>
            </div>
            {_render_progress_bar_html(confidence, color)}
        </div>""",
        unsafe_allow_html=True
    )
    
    # Expert Details
    if st.session_state.get('user_mode') == 'Expert':
        with st.expander("🔬 Technical Details"):
            st.json(prediction_result)

def _render_progress_bar_html(value, color):
    return f"""<div style="background-color: #F1F5F9; border-radius: 99px; height: 6px; width: 100%; margin-top: 15px; overflow: hidden;"><div style="background-color: {color}; width: {value*100}%; height: 100%; border-radius: 99px;"></div></div>"""

