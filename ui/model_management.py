"""Model Management Page for Admin."""

import streamlit as st
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple

from config.settings import settings
from models.model_archiver import ModelArchiver
from models.model_updater import ModelUpdater
from ui.monitoring import _get_training_config

logger = logging.getLogger(__name__)


# =============================================================================
# ADMIN AUTHENTICATION (with rate limiting)
# =============================================================================

# Security: Rate limiting constants
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 300  # 5 minutes


def _get_login_attempts() -> int:
    """Get current failed login attempts count."""
    return st.session_state.get('login_attempts', 0)


def _increment_login_attempts():
    """Increment failed login attempts and set lockout time if exceeded."""
    attempts = _get_login_attempts() + 1
    st.session_state['login_attempts'] = attempts
    if attempts >= MAX_LOGIN_ATTEMPTS:
        st.session_state['lockout_time'] = time.time()


def _reset_login_attempts():
    """Reset login attempts after successful login."""
    st.session_state['login_attempts'] = 0
    st.session_state.pop('lockout_time', None)


def _is_locked_out() -> Tuple[bool, int]:
    """
    Check if user is locked out due to too many failed attempts.
    
    Security: Prevents brute force attacks on admin login.
    Returns: (is_locked, remaining_seconds)
    """
    lockout_time = st.session_state.get('lockout_time', 0)
    if lockout_time == 0:
        return False, 0
    
    elapsed = time.time() - lockout_time
    if elapsed < LOCKOUT_DURATION_SECONDS:
        remaining = int(LOCKOUT_DURATION_SECONDS - elapsed)
        return True, remaining
    
    # Lockout expired, reset
    _reset_login_attempts()
    return False, 0


def _verify_admin_password(input_password: str) -> bool:
    """Verify admin password with constant-time comparison to prevent timing attacks."""
    import hmac
    return hmac.compare_digest(input_password, settings.ADMIN_PASSWORD)


def _check_admin_session() -> bool:
    return st.session_state.get('admin_authenticated', False)


def _login_admin(password: str) -> Tuple[bool, str]:
    """
    Attempt admin login with rate limiting.
    
    Security: Implements rate limiting to prevent brute force attacks.
    Returns: (success, message)
    """
    # Check lockout first
    is_locked, remaining = _is_locked_out()
    if is_locked:
        return False, f"🔒 Terlalu banyak percobaan. Coba lagi dalam {remaining} detik."
    
    if _verify_admin_password(password):
        st.session_state['admin_authenticated'] = True
        st.session_state['admin_login_time'] = time.time()
        _reset_login_attempts()
        return True, "Login sukses!"
    
    _increment_login_attempts()
    attempts_left = MAX_LOGIN_ATTEMPTS - _get_login_attempts()
    if attempts_left > 0:
        return False, f"Password salah! ({attempts_left} percobaan tersisa)"
    return False, "🔒 Akun terkunci. Coba lagi dalam 5 menit."


def _logout_admin():
    st.session_state['admin_authenticated'] = False
    st.session_state.pop('admin_login_time', None)


def _check_session_timeout(timeout_minutes: int = 30) -> bool:
    login_time = st.session_state.get('admin_login_time', 0)
    if login_time == 0:
        return True
    return (time.time() - login_time) > (timeout_minutes * 60)


def render_admin_login_section() -> bool:
    """Render admin login section."""
    if _check_admin_session() and _check_session_timeout(timeout_minutes=30):
        _logout_admin()
        st.warning("⏰ Session timeout. Silakan login kembali.")
    
    if _check_admin_session():
        st.success("✅ **Admin Logged In** - Anda memiliki akses penuh ke fitur manajemen model")
        if st.button("🚪 Logout", key="logout_btn"):
            _logout_admin()
            st.rerun()
    else:
        st.warning("🔒 **Login Required** - Masukkan password admin untuk mengakses fitur manajemen")
        
        # Security: Check if locked out before showing login form
        is_locked, remaining = _is_locked_out()
        if is_locked:
            st.error(f"🔒 Terlalu banyak percobaan gagal. Coba lagi dalam {remaining} detik.")
        else:
            c1, c2 = st.columns([3, 1])
            with c1:
                password = st.text_input(
                    "Password Admin",
                    type="password",
                    placeholder="🔑 Masukkan password...",
                    key="mgmt_admin_pass",
                    label_visibility="collapsed"
                )
            with c2:
                if st.button("🔓 Login", use_container_width=True):
                    if password:
                        success, message = _login_admin(password)
                        if success:
                            st.success(message)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("Isi password!")
    
    return _check_admin_session()


# =============================================================================
# TAB COMPONENTS
# =============================================================================

def render_tutorial_section():
    """Render tutorial section for admin."""
    with st.expander("📚 **TUTORIAL: Cara Upload & Simpan Model** (Klik untuk membuka)", expanded=False):
        st.markdown("""
        ### 📖 Panduan Manajemen Model
        
        **1. Persiapan File**
        - Pastikan file `model_pipeline.pkl` siap.
        
        **2. Login Admin**
        - Gunakan tombol login di atas untuk akses penuh.
        
        **3. Upload Model**
        - Gunakan tab **Update** untuk mengunggah model baru.
        - Isi metrik akurasi agar tercatat di history.
        
        **4. Promosi & Archive**
        - Deploy model dari Staging ke Production di tab **Promosi**.
        - Lihat backup di tab **Archive**.
        """)


def render_upload_model_tab(is_admin: bool, updater: ModelUpdater, archiver: ModelArchiver):
    """Render tab for uploading new model."""
    st.markdown("#### 📤 Upload Model Baru")
    
    if not is_admin:
        st.info("🔒 Login sebagai admin untuk mengupload model baru")
        return
    
    st.caption("Upload model baru (.pkl) untuk menggantikan versi Production saat ini.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**File Model (.pkl):**")
        uploaded_model = st.file_uploader("Upload file model", type=['pkl'], key="upload_model_file", label_visibility="collapsed")
        if uploaded_model:
            st.success(f"✓ {uploaded_model.name}")
    
    with col2:
        st.markdown("**File Preprocessor:**")
        uploaded_preprocessor = st.file_uploader("Upload file preprocessor", type=['pkl'], key="upload_preprocessor_file", label_visibility="collapsed")
        if uploaded_preprocessor:
            st.success(f"✓ {uploaded_preprocessor.name}")
    
    st.markdown("---")
    st.markdown("**📈 Metrics Model Baru:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        new_accuracy = st.number_input("Akurasi Model", 0.0, 1.0, 0.75, 0.01, key="new_accuracy")
    with col2:
        new_f1_score = st.number_input("F1 Score", 0.0, 1.0, 0.73, 0.01, key="new_f1")
    with col3:
        new_training_samples = st.number_input("Training Samples", 100, None, 1000, 100, key="new_samples")
    
    update_reason = st.text_area("📝 Alasan Update Model:", placeholder="Contoh: Optimasi data...", key="update_reason")
    
    st.markdown("---")
    
    if st.button("🚀 Update Model Sekarang", use_container_width=True, type="primary", key="btn_update"):
        if uploaded_model is not None:
            with st.spinner("⏳ Memproses update model..."):
                try:
                    temp_model_dir = Path('temp_model_upload')
                    temp_model_dir.mkdir(exist_ok=True)
                    
                    model_path = temp_model_dir / uploaded_model.name
                    with open(model_path, 'wb') as f:
                        f.write(uploaded_model.getvalue())
                    
                    if uploaded_preprocessor:
                        preprocessor_path = temp_model_dir / uploaded_preprocessor.name
                        with open(preprocessor_path, 'wb') as f:
                            f.write(uploaded_preprocessor.getvalue())
                    
                    new_metrics = {
                        'accuracy': new_accuracy,
                        'f1_score': new_f1_score,
                        'training_samples': new_training_samples,
                        'uploaded_at': datetime.now().isoformat()
                    }
                    
                    success, report = updater.update_model_v1(
                        new_model_path=str(temp_model_dir),
                        new_metrics=new_metrics,
                        update_reason=update_reason or "Update via UI",
                        auto_validate=True
                    )
                    
                    if success:
                        st.success("✅ Model berhasil di-update!")
                        st.json(report.get('summary', {}))
                    else:
                        st.error(f"❌ Update gagal: {report.get('error', 'Unknown')}")
                        st.json(report)
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Silakan upload file model (.pkl) terlebih dahulu")


def render_promotion_tab(is_admin: bool, updater: ModelUpdater, archiver: ModelArchiver, current_version: str):
    """Render tab for model promotion."""
    st.markdown("##### 🎯 Status Production")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**🇮🇩 Model v1 (Indo)**\n\nStage: `Production`\n\n✅ Aktif")
    with col2:
        st.info("**🇺🇸 Model v2 (Eng)**\n\nStage: `Production`\n\n✅ Aktif")
    with col3:
        st.info(f"**📦 Archives**\n\nTotal: {len(archiver.list_archived_models())}\n\nSiap Restore")
    
    if not is_admin:
        st.info("🔒 Login sebagai admin untuk promosi model")
        return
    
    st.divider()
    st.markdown("##### 🔄 Aksi Promosi")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Archive → Production**")
        staging_models_list = archiver.list_archived_models()
        if staging_models_list:
            sel_idx = st.selectbox(
                "Pilih Archive:",
                range(len(staging_models_list)),
                format_func=lambda i: f"{staging_models_list[i]['version']} - {staging_models_list[i]['archived_at'][:10]}",
                key="promo_sel"
            )
            if st.button("⬆️ Restore ke Production", use_container_width=True, key="btn_promo"):
                with st.spinner("Restoring..."):
                    success, res = updater.rollback_to_archive(staging_models_list[sel_idx]['path'])
                    if success:
                        st.success("✅ Restore Berhasil")
                    else:
                        st.error("❌ Restore Gagal")
        else:
            st.info("📭 Tidak ada archive")

    with col2:
        st.markdown("**Production → Archive**")
        note = st.text_input("Catatan:", placeholder="Backup...", key="arch_note")
        if st.button("⬇️ Archive Saat Ini", use_container_width=True, key="btn_arch_now"):
            with st.spinner("Archiving..."):
                try:
                    p = archiver.archive_model(
                        version=current_version,
                        current_model_path='models/saved_model',
                        metrics={},
                        notes=note or "Manual Archive"
                    )
                    st.success(f"✅ Archived to {p}")
                except Exception as e:
                    st.error(f"Error: {e}")


def render_archive_tab(is_admin: bool, updater: ModelUpdater, archiver: ModelArchiver):
    """Render tab for archive management."""
    st.markdown("#### 📦 Archive Management")
    archived = archiver.list_archived_models()
    
    if not archived:
        st.info("📭 Belum ada archive")
        return
    
    for idx, info in enumerate(archived):
        with st.expander(f"📦 {info['version']} - {info['archived_at'][:10]}", expanded=(idx == 0)):
            c1, c2 = st.columns(2)
            c1.markdown(f"**Info**\n\nTime: {info['archived_at']}\n\nNote: {info.get('notes', '-')}")
            metrics = info.get('metrics', {})
            c2.markdown(f"**Metrics**\n\nAcc: {metrics.get('accuracy', 0):.2%}\n\nF1: {metrics.get('f1_score', 0):.2%}")
            
            if is_admin:
                st.divider()
                b1, b2, b3 = st.columns(3)
                if b1.button("🔄 Restore", key=f"r_{idx}"):
                    if updater.rollback_to_archive(info['path'])[0]:
                        st.success("Restored!")
                        st.rerun()
                if b2.button("👁️ Info", key=f"v_{idx}"):
                    st.text(archiver.get_archive_info(info['path']))
                if b3.button("🗑️ Hapus", key=f"d_{idx}"):
                    if archiver.delete_archive(info['path']):
                        st.success("Deleted!")
                        st.rerun()


def render_comparison_tab(archiver: ModelArchiver):
    """Render tab for model comparison."""
    st.markdown("#### ⚖️ Model Comparison")
    st.markdown("**Production vs Archive**")
    
    try:
        config = _get_training_config('models/saved_model/training_config.json')
        curr = config.get('metrics', {})
    except:
        curr = {'accuracy': 0.6972, 'f1_score': 0.6782}

    archives = archiver.list_archived_models()
    
    if not archives:
        st.warning("Butuh minimal 1 archive untuk perbandingan.")
        return
    
    sel = st.selectbox(
        "Pilih Archive:",
        range(len(archives)),
        format_func=lambda i: f"{archives[i]['version']} - {archives[i]['archived_at'][:10]}"
    )
    comp = archives[sel].get('metrics', {})
    
    c1, c2, c3 = st.columns(3)
    diff_acc = curr.get('accuracy', 0) - comp.get('accuracy', 0)
    c1.metric("Akurasi (Prod)", f"{curr.get('accuracy', 0):.2%}", f"{diff_acc:.2%}")
    
    diff_f1 = curr.get('f1_score', 0) - comp.get('f1_score', 0)
    c2.metric("F1 Score (Prod)", f"{curr.get('f1_score', 0):.2%}", f"{diff_f1:.2%}")
    
    c3.caption("Comparison base: Selected Archive")


def render_history_tab(updater: ModelUpdater):
    """Render tab for update history."""
    st.markdown("#### 📋 Update History")
    hist = updater.list_update_history(limit=20)
    
    if hist:
        for h in hist:
            icon = "✅" if h.get('success') else "❌"
            st.text(f"{icon} {h.get('timestamp', '?')[:16]} - {h.get('reason', '-')}")
    else:
        st.info("Belum ada history.")


# =============================================================================
# MAIN PAGE
# =============================================================================

def render_model_management_page():
    """Main function to render Model Management page."""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 25px;">
            <h1 style="font-size: 1.8rem; margin-bottom: 8px;">🚀 Model Management</h1>
            <p style="color: #64748B; font-size: 0.9rem;">Pusat kontrol deployment dan monitoring model AI</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    is_admin = render_admin_login_section()
    st.markdown("---")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📤 Update",
        "🚀 Promosi",
        "📦 Archive",
        "⚖️ Komparasi",
        "📋 History"
    ])
    
    updater = ModelUpdater()
    archiver = ModelArchiver()
    current_version = st.session_state.get('selected_model_version', 'v1')
    
    with tab1:
        render_upload_model_tab(is_admin, updater, archiver)
    with tab2:
        render_promotion_tab(is_admin, updater, archiver, current_version)
    with tab3:
        render_archive_tab(is_admin, updater, archiver)
    with tab4:
        render_comparison_tab(archiver)
    with tab5:
        render_history_tab(updater)
    
    st.markdown("<br>", unsafe_allow_html=True)
    render_tutorial_section()
