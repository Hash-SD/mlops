"""UI module for MLOps Streamlit Text AI application."""

from ui.styles import load_css
from ui.sidebar import render_sidebar
from ui.main_area import (
    render_main_layout,
    render_empty_state,
    render_result_section,
    render_example_buttons,
    render_feedback_section
)
from ui.monitoring import render_monitoring_dashboard
from ui.model_management import render_model_management_page
from ui.cicd_management import render_cicd_tab, GitHubIntegration

__all__ = [
    'load_css',
    'render_sidebar',
    'render_main_layout',
    'render_empty_state',
    'render_result_section',
    'render_example_buttons',
    'render_feedback_section',
    'render_monitoring_dashboard',
    'render_model_management_page',
    'render_cicd_tab',
    'GitHubIntegration'
]
