"""Model Management Page for Admin - Standard Streamlit UI."""

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
from ui.cicd_management import render_cicd_tab

logger = logging.getLogger(__name__)

# Security constants
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 300


def _get_login_attempts() -> int:
    return st.session_state.get('login_attempts', 0)


def _increment_login_attempts():
    attempts = _get_login_attempts() + 1
    st.session_state['login_attempts'] = attempts
    if attempts >= MAX_LOGIN_ATTEMPTS:
        st.session_state['lockout_time'] = time.time()


def _reset_login_attempts():
    st.session_state['login_attempts'] = 0
    st.session_state.pop('lockout_time', None)


def _is_locked_out() -> Tuple[bool, int]:
    lockout_time = st.session_state.get('lockout_time', 0)
    if lockout_time == 0:
        return False, 0
    elapsed = time.time() - lockout_time
    if elapsed < LOCKOUT_DURATION_SECONDS:
        return True, int(LOCKOUT_DURATION_SECONDS - elapsed)
    _reset_login_attempts()
    return False, 0


def _verify_admin_password(input_password: str) -> bool:
    import hmac
    return hmac.compare_digest(input_password, settings.ADMIN_PASSWORD)


def _check_admin_session() -> bool:
    return st.session_state.get('admin_authenticated', False)


def _login_admin(password: str) -> Tuple[bool, str]:
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
    """Render admin login section with standard Streamlit components."""
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
        
        is_locked, remaining = _is_locked_out()
        if is_locked:
            st.error(f"🔒 Terlalu banyak percobaan gagal. Coba lagi dalam {remaining} detik.")
        else:
            col1, col2 = st.columns([3, 1])
            with col1:
                password = st.text_input(
                    "Password Admin",
                    type="password",
                    placeholder="🔑 Masukkan password...",
                    key="mgmt_admin_pass",
                    label_visibility="collapsed"
                )
            with col2:
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


def render_tutorial_section():
    """Render tutorial section for admin."""
    with st.expander("📚 **TUTORIAL: Panduan Lengkap Model Management** (Klik untuk membuka)", expanded=False):
        st.markdown("""
        ### 📖 Panduan Manajemen Model InsighText
        
        ---
        
        #### 1️⃣ Persiapan Sebelum Upload
        
        **File yang Diperlukan:**
        - `model.pkl` - File model machine learning (Naive Bayes/TF-IDF)
        - `preprocessor.pkl` - File preprocessor (opsional)
        
        **Metrik yang Harus Disiapkan:**
        - Akurasi model (0.0 - 1.0)
        - F1 Score (0.0 - 1.0)
        - Jumlah training samples
        
        ---
        
        #### 2️⃣ Proses Upload Model
        
        1. **Login sebagai Admin** - Masukkan password admin
        2. **Buka Tab "📤 Update"**
        3. **Upload file model** (.pkl)
        4. **Isi metrik** akurasi, F1 score, dan training samples
        5. **Atur rasio data** training/testing (default 70:30)
        6. **Centang "Auto Push ke GitHub"** jika ingin otomatis push
        7. **Klik "🚀 Update Model Sekarang"**
        
        ---
        
        #### 3️⃣ Alur Data Training (Feedback Loop)
        
        ```
        User Input → Prediksi → Feedback (✅/❌) → Database
                                                    ↓
        Model Baru ← Retraining ← Data Training ←──┘
        ```
        
        **Cara Kerja:**
        - User memberikan feedback pada hasil prediksi
        - Data dengan feedback disimpan di database
        - Admin dapat mengatur rasio split (Training:Testing)
        - Data digunakan untuk retraining model
        
        ---
        
        #### 4️⃣ CI/CD Integration (GitHub)
        
        **Konfigurasi (sudah di Streamlit Secrets):**
        - `GITHUB_TOKEN` - Personal Access Token
        - `GITHUB_REPO` - Format: `owner/repo-name`
        
        **Fitur CI/CD:**
        - ✅ Auto push model ke GitHub setelah upload
        - ✅ Create release dengan version tag
        - ✅ Trigger GitHub Actions workflow
        - ✅ Monitoring CI/CD runs
        
        ---
        
        #### 5️⃣ Promosi & Archive
        
        **Archive Model:**
        - Backup model sebelum update
        - Simpan dengan catatan/notes
        
        **Restore Model:**
        - Kembalikan model dari archive
        - Rollback jika model baru bermasalah
        
        ---
        
        #### 6️⃣ Monitoring Feedback
        
        **Statistik yang Tersedia:**
        - Total prediksi
        - Jumlah feedback (positif/negatif)
        - Akurasi berdasarkan feedback user
        - Data siap untuk retraining
        
        ---
        
        #### ⚠️ Tips Penting
        
        1. **Selalu backup** model sebelum update
        2. **Isi metrik dengan benar** untuk tracking performa
        3. **Gunakan semantic versioning** (v1.0.0, v1.1.0, v2.0.0)
        4. **Monitor feedback** untuk evaluasi model
        5. **Atur rasio data** sesuai kebutuhan (70:30 recommended)
        """)


def render_upload_model_tab(is_admin: bool, updater: ModelUpdater, archiver: ModelArchiver):
    """Render tab for uploading new model with GitHub integration."""
    st.markdown("#### 📤 Upload Model Baru")
    
    if not is_admin:
        st.info("🔒 Login sebagai admin untuk mengupload model baru")
        return
    
    st.caption("Upload model baru (.pkl) untuk menggantikan versi Production saat ini.")
    
    # File Upload Section
    st.markdown("**📁 Upload Files**")
    
    uploaded_model = st.file_uploader(
        "File Model (.pkl)",
        type=['pkl'],
        key="upload_model_file",
        help="Upload file model machine learning"
    )
    if uploaded_model:
        st.success(f"✓ {uploaded_model.name}")
    
    uploaded_preprocessor = st.file_uploader(
        "File Preprocessor (opsional)",
        type=['pkl'],
        key="upload_preprocessor_file",
        help="Upload file preprocessor jika ada"
    )
    if uploaded_preprocessor:
        st.success(f"✓ {uploaded_preprocessor.name}")
    
    st.markdown("---")
    
    # Metrics Section
    st.markdown("**📈 Metrics Model Baru**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        new_accuracy = st.number_input("Akurasi Model", 0.0, 1.0, 0.75, 0.01, key="new_accuracy")
    with col2:
        new_f1_score = st.number_input("F1 Score", 0.0, 1.0, 0.73, 0.01, key="new_f1")
    with col3:
        new_training_samples = st.number_input("Training Samples", 100, None, 1000, 100, key="new_samples")
    
    st.markdown("---")
    
    # Data Flow Configuration
    st.markdown("**📊 Konfigurasi Aliran Data:**")
    col1, col2 = st.columns(2)
    
    with col1:
        train_ratio = st.slider(
            "Rasio Data Training",
            min_value=50,
            max_value=90,
            value=70,
            step=5,
            key="upload_train_ratio",
            help="Persentase data feedback yang digunakan untuk training"
        )
    
    with col2:
        st.metric("Training : Testing", f"{train_ratio}% : {100-train_ratio}%")
    
    st.markdown("---")
    
    # GitHub Integration Options
    st.markdown("**🔄 GitHub CI/CD Options:**")
    col1, col2 = st.columns(2)
    
    with col1:
        auto_push_github = st.checkbox(
            "Auto Push ke GitHub",
            value=True,
            key="auto_push_github",
            help="Otomatis push model ke GitHub setelah upload berhasil"
        )
    
    with col2:
        trigger_cicd = st.checkbox(
            "Trigger CI/CD Pipeline",
            value=True,
            key="trigger_cicd_checkbox",
            help="Otomatis trigger GitHub Actions workflow"
        )
    
    if auto_push_github:
        col1, col2 = st.columns(2)
        with col1:
            release_tag = st.text_input(
                "Version Tag",
                value=f"v{datetime.now().strftime('%Y%m%d.%H%M')}",
                key="upload_release_tag",
                help="Tag untuk release (e.g., v1.0.0)"
            )
        with col2:
            release_name = st.text_input(
                "Release Name",
                value=f"Model Update - {datetime.now().strftime('%d %B %Y')}",
                key="upload_release_name"
            )
    
    st.markdown("---")
    
    # Update Reason
    update_reason = st.text_area(
        "📝 Alasan Update Model:",
        placeholder="Contoh: Penambahan data training baru, optimasi hyperparameter...",
        key="update_reason"
    )
    
    st.markdown("---")
    
    # Upload Button
    if st.button("🚀 Update Model Sekarang", use_container_width=True, type="primary", key="btn_update"):
        if uploaded_model is not None:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: Save model locally
                status_text.text("📁 Menyimpan model...")
                progress_bar.progress(20)
                
                temp_model_dir = Path('temp_model_upload')
                temp_model_dir.mkdir(exist_ok=True)
                
                model_path = temp_model_dir / uploaded_model.name
                with open(model_path, 'wb') as f:
                    f.write(uploaded_model.getvalue())
                
                if uploaded_preprocessor:
                    preprocessor_path = temp_model_dir / uploaded_preprocessor.name
                    with open(preprocessor_path, 'wb') as f:
                        f.write(uploaded_preprocessor.getvalue())
                
                # Step 2: Update model
                status_text.text("🔄 Memproses update model...")
                progress_bar.progress(40)
                
                new_metrics = {
                    'accuracy': new_accuracy,
                    'f1_score': new_f1_score,
                    'training_samples': new_training_samples,
                    'train_ratio': train_ratio,
                    'uploaded_at': datetime.now().isoformat()
                }
                
                success, report = updater.update_model_v1(
                    new_model_path=str(temp_model_dir),
                    new_metrics=new_metrics,
                    update_reason=update_reason or "Update via UI",
                    auto_validate=True
                )
                
                if not success:
                    st.error(f"❌ Update gagal: {report.get('error', 'Unknown')}")
                    st.json(report)
                    return
                
                progress_bar.progress(60)
                st.success("✅ Model berhasil di-update secara lokal!")
                
                # Step 3: Push to GitHub (if enabled)
                if auto_push_github:
                    status_text.text("📤 Push ke GitHub...")
                    progress_bar.progress(80)
                    
                    from ui.cicd_management import GitHubIntegration
                    from config.settings import get_config_value
                    
                    token = get_config_value('GITHUB_TOKEN', '')
                    repo = get_config_value('GITHUB_REPO', '')
                    
                    gh = GitHubIntegration(token, repo)
                    
                    if gh.is_configured():
                        release_notes = f"""## Model Update
                        
**Metrics:**
- Accuracy: {new_accuracy:.2%}
- F1 Score: {new_f1_score:.2%}
- Training Samples: {new_training_samples}
- Train/Test Ratio: {train_ratio}:{100-train_ratio}

**Reason:** {update_reason or 'Update via UI'}

**Uploaded at:** {datetime.now().isoformat()}
"""
                        gh_success, gh_message = gh.create_release(
                            release_tag,
                            release_name,
                            release_notes
                        )
                        
                        if gh_success:
                            st.success(f"✅ GitHub: {gh_message}")
                        else:
                            st.warning(f"⚠️ GitHub: {gh_message}")
                        
                        # Step 4: Trigger CI/CD (if enabled)
                        if trigger_cicd:
                            status_text.text("⚡ Trigger CI/CD Pipeline...")
                            cicd_success, cicd_message = gh.trigger_workflow(
                                'model-deploy.yml',
                                inputs={'train_ratio': str(train_ratio)}
                            )
                            if cicd_success:
                                st.success(f"✅ CI/CD: {cicd_message}")
                            else:
                                st.warning(f"⚠️ CI/CD: {cicd_message}")
                    else:
                        st.warning("⚠️ GitHub tidak dikonfigurasi. Model hanya disimpan lokal.")
                
                progress_bar.progress(100)
                status_text.text("✅ Selesai!")
                
                # Show summary
                st.markdown("---")
                st.markdown("**📋 Summary:**")
                col1, col2, col3 = st.columns(3)
                col1.metric("Accuracy", f"{new_accuracy:.1%}")
                col2.metric("F1 Score", f"{new_f1_score:.1%}")
                col3.metric("Data Split", f"{train_ratio}:{100-train_ratio}")
                
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


def render_feedback_stats_tab(db_manager=None):
    """Render feedback statistics tab."""
    st.markdown("#### 📊 Feedback Statistics")
    st.caption("Statistik feedback dari pengguna untuk evaluasi model")
    
    if not db_manager or not hasattr(db_manager, 'get_feedback_stats'):
        st.info("📭 Fitur feedback statistics tidak tersedia")
        return
    
    stats = db_manager.get_feedback_stats()
    
    if not stats or stats.get('total_predictions', 0) == 0:
        st.info("📭 Belum ada data feedback")
        return
    
    # Stats metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Prediksi", stats.get('total_predictions', 0))
    col2.metric("Dengan Feedback", stats.get('with_feedback', 0))
    col3.metric("✅ Benar", stats.get('positive_feedback', 0))
    col4.metric("❌ Salah", stats.get('negative_feedback', 0))
    
    # Accuracy from feedback
    if stats.get('with_feedback', 0) > 0:
        feedback_accuracy = stats.get('positive_feedback', 0) / stats.get('with_feedback', 1)
        st.markdown("---")
        st.metric("📈 Akurasi Berdasarkan Feedback", f"{feedback_accuracy:.1%}")
        
        # Progress bar
        st.progress(feedback_accuracy)


def render_model_management_page(db_manager=None):
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
    
    # Tutorial section - moved to top (below login)
    render_tutorial_section()
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Upload",
        "Promosi",
        "Archive",
        "Komparasi",
        "History",
        "CI/CD",
        "Feedback"
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
    with tab6:
        render_cicd_tab(is_admin, db_manager)
    with tab7:
        render_feedback_stats_tab(db_manager)
