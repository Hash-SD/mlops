"""CI/CD and GitHub Integration for Model Management - Standard Streamlit UI."""

import streamlit as st
import logging
import os
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class GitHubIntegration:
    """Handle GitHub operations for model versioning."""
    
    def __init__(self, token: Optional[str] = None, repo: Optional[str] = None):
        self.token = token or os.getenv('GITHUB_TOKEN', '')
        self.repo = repo or os.getenv('GITHUB_REPO', '')
        self.api_base = 'https://api.github.com'
    
    def is_configured(self) -> bool:
        """Check if GitHub integration is properly configured."""
        return bool(self.token and self.repo)
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests."""
        return {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test GitHub API connection."""
        if not self.is_configured():
            return False, "GitHub token atau repository belum dikonfigurasi"
        
        try:
            import httpx
            url = f"{self.api_base}/repos/{self.repo}"
            r = httpx.get(url, headers=self.get_headers(), timeout=10)
            
            if r.status_code == 200:
                return True, f"Terhubung ke {self.repo}"
            elif r.status_code == 401:
                return False, "Token tidak valid"
            elif r.status_code == 404:
                return False, "Repository tidak ditemukan"
            else:
                return False, f"Error: {r.status_code}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def create_release(self, tag: str, name: str, body: str, files: list = None) -> Tuple[bool, str]:
        """Create a new release on GitHub."""
        if not self.is_configured():
            return False, "GitHub tidak dikonfigurasi"
        
        try:
            import httpx
            
            url = f"{self.api_base}/repos/{self.repo}/releases"
            data = {
                'tag_name': tag,
                'name': name,
                'body': body,
                'draft': False,
                'prerelease': False
            }
            
            r = httpx.post(url, headers=self.get_headers(), json=data, timeout=30)
            
            if r.status_code == 201:
                return True, f"Release {tag} berhasil dibuat"
            else:
                return False, f"Gagal membuat release: {r.text}"
                
        except Exception as e:
            logger.error(f"Error creating release: {e}")
            return False, str(e)
    
    def trigger_workflow(self, workflow_id: str, ref: str = 'main', inputs: Dict = None) -> Tuple[bool, str]:
        """Trigger a GitHub Actions workflow."""
        if not self.is_configured():
            return False, "GitHub tidak dikonfigurasi"
        
        try:
            import httpx
            
            url = f"{self.api_base}/repos/{self.repo}/actions/workflows/{workflow_id}/dispatches"
            data = {
                'ref': ref,
                'inputs': inputs or {}
            }
            
            r = httpx.post(url, headers=self.get_headers(), json=data, timeout=30)
            
            if r.status_code == 204:
                return True, f"Workflow {workflow_id} berhasil di-trigger"
            else:
                return False, f"Gagal trigger workflow: {r.text}"
                
        except Exception as e:
            logger.error(f"Error triggering workflow: {e}")
            return False, str(e)
    
    def get_workflow_runs(self, limit: int = 5) -> list:
        """Get recent workflow runs."""
        if not self.is_configured():
            return []
        
        try:
            import httpx
            
            url = f"{self.api_base}/repos/{self.repo}/actions/runs?per_page={limit}"
            r = httpx.get(url, headers=self.get_headers(), timeout=10)
            
            if r.status_code == 200:
                return r.json().get('workflow_runs', [])
            return []
            
        except Exception as e:
            logger.error(f"Error getting workflow runs: {e}")
            return []


def render_cicd_tab(is_admin: bool, db_manager=None):
    """Render CI/CD and GitHub integration tab with standard Streamlit UI."""
    st.markdown("#### 🔄 CI/CD & GitHub Integration")
    
    if not is_admin:
        st.info("🔒 Login sebagai admin untuk mengakses fitur CI/CD")
        return
    
    # Import settings
    from config.settings import get_config_value
    
    # Get GitHub config from secrets/env
    default_token = get_config_value('GITHUB_TOKEN', '')
    default_repo = get_config_value('GITHUB_REPO', '')
    
    # Show connection status
    if default_token and default_repo:
        st.success(f"✅ GitHub terkonfigurasi: `{default_repo}`")
    else:
        st.warning("⚠️ GitHub belum dikonfigurasi di Streamlit Secrets")
    
    # GitHub Configuration Section
    with st.expander("⚙️ Konfigurasi GitHub (Override)", expanded=False):
        st.caption("Kosongkan untuk menggunakan nilai dari Streamlit Secrets")
        
        col1, col2 = st.columns(2)
        with col1:
            github_token = st.text_input(
                "GitHub Token (override)",
                type="password",
                placeholder="Gunakan dari secrets...",
                key="github_token_input",
                help="Kosongkan untuk menggunakan GITHUB_TOKEN dari secrets"
            )
        with col2:
            github_repo = st.text_input(
                "Repository (override)",
                placeholder="Gunakan dari secrets...",
                key="github_repo_input",
                help="Kosongkan untuk menggunakan GITHUB_REPO dari secrets"
            )
        
        if st.button("🔗 Test Koneksi", key="test_github"):
            token = github_token or default_token
            repo = github_repo or default_repo
            gh = GitHubIntegration(token, repo)
            success, message = gh.test_connection()
            if success:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")
    
    st.markdown("---")
    
    # Data Split Control Section
    st.markdown("##### 📊 Kontrol Pembagian Data Training")
    st.caption("Atur rasio pembagian data untuk training dan testing model")
    
    train_ratio = st.slider(
        "Rasio Data Training (%)",
        min_value=50,
        max_value=90,
        value=70,
        step=5,
        key="train_ratio_slider",
        help="Persentase data yang digunakan untuk training"
    )
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Training", f"{train_ratio}%")
    col2.metric("Testing", f"{100-train_ratio}%")
    col3.metric("Ratio", f"{train_ratio}:{100-train_ratio}")
    
    # Get Training Data Stats
    if db_manager and hasattr(db_manager, 'get_training_data'):
        if st.button("📈 Lihat Data Training", key="view_training_data"):
            with st.spinner("Mengambil data..."):
                data = db_manager.get_training_data(train_ratio / 100)
                stats = data.get('stats', {})
                
                if stats.get('total', 0) > 0:
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Data", stats.get('total', 0))
                    col2.metric("Data Training", stats.get('train_count', 0))
                    col3.metric("Data Testing", stats.get('test_count', 0))
                else:
                    st.info("Belum ada data dengan feedback untuk training")
    
    st.markdown("---")
    
    # Model Push Section
    st.markdown("##### 🚀 Push Model ke GitHub")
    
    col1, col2 = st.columns(2)
    
    with col1:
        release_tag = st.text_input(
            "Tag Version",
            placeholder="v1.0.0",
            key="release_tag",
            help="Semantic versioning (e.g., v1.0.0)"
        )
    
    with col2:
        release_name = st.text_input(
            "Release Name",
            placeholder="Model Update - December 2025",
            key="release_name"
        )
    
    release_notes = st.text_area(
        "Release Notes",
        placeholder="Deskripsi perubahan model...",
        key="release_notes",
        height=100
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Push & Create Release", type="primary", use_container_width=True, key="push_release"):
            if not release_tag or not release_name:
                st.warning("⚠️ Isi tag dan nama release")
            else:
                with st.spinner("Membuat release..."):
                    token = st.session_state.get('github_token_input', '') or default_token
                    repo = st.session_state.get('github_repo_input', '') or default_repo
                    gh = GitHubIntegration(token, repo)
                    
                    if not gh.is_configured():
                        st.error("❌ Konfigurasi GitHub terlebih dahulu")
                    else:
                        success, message = gh.create_release(
                            release_tag,
                            release_name,
                            release_notes or "Model update"
                        )
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
    
    with col2:
        if st.button("⚡ Trigger CI/CD Pipeline", use_container_width=True, key="trigger_cicd"):
            with st.spinner("Triggering workflow..."):
                token = st.session_state.get('github_token_input', '') or default_token
                repo = st.session_state.get('github_repo_input', '') or default_repo
                gh = GitHubIntegration(token, repo)
                
                if not gh.is_configured():
                    st.error("❌ Konfigurasi GitHub terlebih dahulu")
                else:
                    success, message = gh.trigger_workflow(
                        'model-deploy.yml',
                        inputs={'train_ratio': str(train_ratio)}
                    )
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
    
    st.markdown("---")
    
    # Recent Workflow Runs
    st.markdown("##### 📋 Recent CI/CD Runs")
    
    token = st.session_state.get('github_token_input', '') or default_token
    repo = st.session_state.get('github_repo_input', '') or default_repo
    gh = GitHubIntegration(token, repo)
    
    if gh.is_configured():
        if st.button("🔄 Refresh", key="refresh_runs"):
            st.rerun()
        
        runs = gh.get_workflow_runs(5)
        if runs:
            for run in runs:
                status = run.get('conclusion', run.get('status', 'unknown'))
                if status == 'success':
                    st.success(f"✅ **{run.get('name', 'Workflow')}** - {run.get('created_at', '')[:10]}")
                elif status == 'failure':
                    st.error(f"❌ **{run.get('name', 'Workflow')}** - {run.get('created_at', '')[:10]}")
                else:
                    st.warning(f"🔄 **{run.get('name', 'Workflow')}** - {run.get('created_at', '')[:10]} ({status})")
        else:
            st.info("Tidak ada workflow runs terbaru")
    else:
        st.info("💡 Konfigurasi GitHub untuk melihat CI/CD runs")
