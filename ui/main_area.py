"""Main area components for Single Column Vertical Layout."""

import streamlit as st
from typing import Dict, Any, Tuple
from config.settings import settings


def render_main_layout() -> Tuple[str, bool]:
    """
    Render the main content area.
    
    Returns:
        Tuple of (text_input, analyze_clicked)
    """
    # Header
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="font-size: 1.8rem; margin-bottom: 5px;">✨ Identifikasi Sentimen</h1>
            <span class="subtitle-text">Analisis sentimen dari teks secara instan.</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Input Section - Dynamic based on selected model
    selected_model = st.session_state.get('selected_model_version', 'v1')
    
    if selected_model == 'v2':
        input_label = "### 📝 Input English Text"
        placeholder_text = "Enter a review with at least 7 words or choose an example below..."
    else:
        input_label = "### 📝 Input Teks Bahasa Indonesia"
        placeholder_text = "Masukkan ulasan minimal 7 kata atau pilih contoh di bawah..."
    
    st.markdown(input_label)
    
    if 'text_input_area' not in st.session_state:
        st.session_state.text_input_area = ""

    text_input = st.text_area(
        "Input Text",
        value=st.session_state.text_input_area,
        height=150,
        placeholder=placeholder_text,
        label_visibility="collapsed"
    )
    
    # Word count validation
    word_count = len(text_input.split()) if text_input else 0
    min_words = settings.MIN_WORDS
    is_valid_input = word_count >= min_words
    
    # Display input info
    if text_input:
        if is_valid_input:
            st.caption(f"✅ {word_count} kata | {len(text_input)}/{settings.MAX_INPUT_LENGTH} karakter")
        else:
            st.warning(f"⚠️ Input minimal {min_words} kata. Saat ini: {word_count} kata (kurang {min_words - word_count} kata lagi)")
    
    analyze_clicked = st.button(
        "🔍 Analisis Sekarang",
        type="primary",
        use_container_width=True,
        disabled=not is_valid_input
    )
    
    return text_input, analyze_clicked


def render_empty_state():
    """Render the dotted empty state box."""
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
    """Render example text buttons."""
    st.markdown("### 🧪 Coba Contoh Teks")
    st.caption("Tidak punya teks? Klik salah satu tombol di bawah untuk mencoba demo:")
    
    selected_model = st.session_state.get('selected_model_version', 'v1')
    
    # Language-specific examples
    if selected_model == 'v2':
        examples = [
            ("👍 Positive", "This product is amazing! It has greatly improved my daily workflow.", "v2"),
            ("👎 Negative", "Very disappointing, the app crashes frequently and runs slowly.", "v2"),
        ]
    else:
        examples = [
            ("👍 Positif", "Luar biasa! Produk ini sangat membantu pekerjaan saya sehari-hari.", "v1"),
            ("👎 Negatif", "Sangat mengecewakan, aplikasi sering crash dan lambat.", "v1"),
            ("😐 Netral", "Pengiriman standar, barang sampai sesuai estimasi waktu.", "v1")
        ]
    
    cols = st.columns(len(examples))
    for i, (label, text, ver) in enumerate(examples):
        if cols[i].button(label, key=f"ex_btn_{i}", use_container_width=True):
            st.session_state.text_input_area = text
            st.rerun()


def render_result_section(prediction_result: Dict[str, Any], db_manager=None):
    """Render results in a clean glass card with feedback option."""
    if not prediction_result:
        return

    pred_label = prediction_result.get('prediction', 'Unknown')
    confidence = prediction_result.get('confidence', 0.0)
    prediction_id = prediction_result.get('prediction_id')
    
    # Color mapping
    color_map = {
        'positif': ('#10B981', '😊'),
        'positive': ('#10B981', '😊'),
        'negatif': ('#EF4444', '😠'),
        'negative': ('#EF4444', '😠'),
        'netral': ('#F59E0B', '😐')
    }
    
    color, icon = color_map.get(pred_label.lower(), ('#64748B', '❓'))
    progress_width = min(confidence * 100, 100)
    
    st.markdown(
        f"""<div class="glass-card" style="border-left: 5px solid {color}; margin-top: 20px;">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div style="flex: 1; min-width: 0;">
                    <p style="color: #64748B; margin-bottom: 5px; font-size: 1rem;">Hasil Analisis</p>
                    <h2 style="color: {color}; margin: 0; display: flex; align-items: center; gap: 8px; font-size: 1.2rem; word-break: keep-all;">
                        <span style="font-size: 1.2rem;">{icon}</span> {pred_label.upper()}
                    </h2>
                </div>
                <div style="text-align: right; flex-shrink: 0;">
                    <span class="confidence-value">{confidence:.0%}</span>
                    <span class="confidence-label">Confidence</span>
                </div>
            </div>
            <div style="background-color: #F1F5F9; border-radius: 99px; height: 6px; width: 100%; margin-top: 15px; overflow: hidden;">
                <div style="background-color: {color}; width: {progress_width}%; height: 100%; border-radius: 99px;"></div>
            </div>
        </div>""",
        unsafe_allow_html=True
    )
    
    # Show database warning if exists
    metadata = prediction_result.get('metadata', {})
    if metadata.get('database_warning'):
        st.warning(f"⚠️ {metadata['database_warning']} - Feedback tidak tersedia untuk prediksi ini. Coba refresh halaman atau periksa koneksi database.")
    elif metadata.get('database_info'):
        st.info(f"ℹ️ {metadata['database_info']} - Feedback tidak tersedia.")
    
    # Feedback Section - Only show if user consent is given and prediction was saved
    if prediction_id and st.session_state.get('user_consent', True):
        render_feedback_section(prediction_id, db_manager)
    
    # Expert Details
    if st.session_state.get('user_mode') == 'Expert':
        with st.expander("🔬 Technical Details"):
            st.json(prediction_result)


def render_feedback_section(prediction_id: int, db_manager=None):
    """Render feedback buttons for user to rate prediction accuracy."""
    feedback_key = f"feedback_{prediction_id}"
    
    # Check if feedback already given
    feedback_value = st.session_state.get(feedback_key)
    if feedback_value:
        # Tampilkan hasil feedback dengan jelas
        if feedback_value == 'correct':
            st.markdown(
                """
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 12px; margin-top: 10px; text-align: center;">
                    <span style="color: #166534; font-weight: 600;">✅ Feedback: BENAR</span>
                    <p style="color: #166534; font-size: 0.85rem; margin: 5px 0 0 0;">Terima kasih! Prediksi dinilai akurat.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:  # feedback_value == 'wrong'
            st.markdown(
                """
                <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 12px; margin-top: 10px; text-align: center;">
                    <span style="color: #DC2626; font-weight: 600;">❌ Feedback: SALAH</span>
                    <p style="color: #DC2626; font-size: 0.85rem; margin: 5px 0 0 0;">Terima kasih! Data akan digunakan untuk perbaikan model.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        return
    
    st.markdown(
        """
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #E2E8F0;">
            <p style="color: #64748B; font-size: 0.9rem; margin-bottom: 10px;">
                📝 Apakah hasil prediksi ini akurat? <span style="color: #94A3B8; font-size: 0.8rem;">(opsional)</span>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("✅ Benar", key=f"fb_correct_{prediction_id}", use_container_width=True):
            success = False
            if db_manager and hasattr(db_manager, 'update_prediction_feedback'):
                success = db_manager.update_prediction_feedback(prediction_id, True)
            st.session_state[feedback_key] = 'correct'
            if not success:
                st.session_state[f"feedback_db_error_{prediction_id}"] = True
            st.rerun()
    
    with col2:
        if st.button("❌ Salah", key=f"fb_wrong_{prediction_id}", use_container_width=True):
            success = False
            if db_manager and hasattr(db_manager, 'update_prediction_feedback'):
                success = db_manager.update_prediction_feedback(prediction_id, False)
            st.session_state[feedback_key] = 'wrong'
            if not success:
                st.session_state[f"feedback_db_error_{prediction_id}"] = True
            st.rerun()
