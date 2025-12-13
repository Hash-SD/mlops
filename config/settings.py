"""
Configuration management for MLOps Streamlit Text AI application.

Centralized configuration using dataclass and environment variables.
Supports Streamlit secrets for cloud deployment.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
except ImportError:
    pass

# Streamlit secrets support
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get configuration value from environment or Streamlit secrets.
    Priority: Environment variables > Streamlit secrets > Default
    """
    value = os.getenv(key)
    if value is not None:
        return value
    
    if HAS_STREAMLIT and hasattr(st, 'secrets'):
        try:
            value = st.secrets.get(key)
            if value is not None:
                return str(value)
        except Exception:
            pass
    
    return default


@dataclass
class Settings:
    """Application settings with environment variable support."""
    
    # Database
    DATABASE_TYPE: str = field(default_factory=lambda: get_config_value('DATABASE_TYPE', 'sqlite'))
    DATABASE_URL: str = field(default_factory=lambda: get_config_value('DATABASE_URL', 'sqlite:///mlops_app.db'))
    SUPABASE_URL: str = field(default_factory=lambda: get_config_value('SUPABASE_URL', ''))
    SUPABASE_KEY: str = field(default_factory=lambda: get_config_value('SUPABASE_KEY', ''))
    
    # MLflow
    MLFLOW_TRACKING_URI: str = field(default_factory=lambda: get_config_value('MLFLOW_TRACKING_URI', 'http://localhost:5000'))
    MLFLOW_EXPERIMENT_NAME: str = field(default_factory=lambda: get_config_value('MLFLOW_EXPERIMENT_NAME', 'text-ai-system'))
    
    # Application
    APP_TITLE: str = field(default_factory=lambda: os.getenv('APP_TITLE', 'Sistem AI Berbasis Teks'))
    APP_ICON: str = field(default_factory=lambda: os.getenv('APP_ICON', '🔎'))
    MAX_INPUT_LENGTH: int = field(default_factory=lambda: int(os.getenv('MAX_INPUT_LENGTH', '5000')))
    MIN_INPUT_LENGTH: int = field(default_factory=lambda: int(os.getenv('MIN_INPUT_LENGTH', '3')))
    MIN_WORDS: int = field(default_factory=lambda: int(os.getenv('MIN_WORDS', '7')))
    
    # Model
    MODEL_VERSIONS: List[str] = field(default_factory=lambda: ['v1', 'v2'])
    DEFAULT_MODEL_VERSION: str = field(default_factory=lambda: os.getenv('DEFAULT_MODEL_VERSION', 'v2'))
    
    # Logging
    LOG_FILE: str = field(default_factory=lambda: os.getenv('LOG_FILE', 'app.log'))
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    
    # Monitoring
    PREDICTION_HISTORY_LIMIT: int = field(default_factory=lambda: int(os.getenv('PREDICTION_HISTORY_LIMIT', '10')))
    LATENCY_THRESHOLD_MS: float = field(default_factory=lambda: float(os.getenv('LATENCY_THRESHOLD_MS', '5000.0')))
    
    # Database Retry
    DB_MAX_RETRIES: int = field(default_factory=lambda: int(os.getenv('DB_MAX_RETRIES', '3')))
    DB_RETRY_DELAY: float = field(default_factory=lambda: float(os.getenv('DB_RETRY_DELAY', '1.0')))
    
    # Privacy & Admin
    ENABLE_PII_DETECTION: bool = field(default_factory=lambda: os.getenv('ENABLE_PII_DETECTION', 'true').lower() == 'true')
    ADMIN_PASSWORD: str = field(default_factory=lambda: get_config_value('ADMIN_PASSWORD', 'admin123secure'))
    
    def __post_init__(self):
        self._validate()
    
    def _validate(self):
        """Validate configuration values."""
        if self.MIN_INPUT_LENGTH < 1:
            raise ValueError("MIN_INPUT_LENGTH must be at least 1")
        if self.MAX_INPUT_LENGTH < self.MIN_INPUT_LENGTH:
            raise ValueError("MAX_INPUT_LENGTH must be greater than MIN_INPUT_LENGTH")
        if self.DEFAULT_MODEL_VERSION not in self.MODEL_VERSIONS:
            raise ValueError(f"DEFAULT_MODEL_VERSION '{self.DEFAULT_MODEL_VERSION}' must be one of {self.MODEL_VERSIONS}")
        
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.LOG_LEVEL.upper() not in valid_log_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_log_levels}")
        if self.DB_MAX_RETRIES < 1:
            raise ValueError("DB_MAX_RETRIES must be at least 1")
        if self.DB_RETRY_DELAY < 0:
            raise ValueError("DB_RETRY_DELAY must be non-negative")
    
    def get_database_path(self) -> str:
        """Extract database file path from DATABASE_URL."""
        if self.DATABASE_URL.startswith('sqlite:///'):
            return self.DATABASE_URL.replace('sqlite:///', '')
        return self.DATABASE_URL
    
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith('sqlite://')
    
    def is_postgresql(self) -> bool:
        return self.DATABASE_URL.startswith('postgresql://')
    
    def is_supabase(self) -> bool:
        return self.DATABASE_TYPE.lower() == 'supabase'


# Global settings instance
settings = Settings()


def reload_settings() -> Settings:
    """Reload settings from environment variables."""
    global settings
    settings = Settings()
    return settings
