import pytest
from config import Settings, get_settings, ensure_directories
import os
from pathlib import Path


def test_settings_defaults():
    """Test default settings values."""
    settings = Settings()
    
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000
    assert settings.api_version == "v1"
    assert settings.max_batch_size == 100
    assert settings.log_level == "INFO"


def test_settings_from_env(monkeypatch):
    """Test settings loading from environment variables."""
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MAX_BATCH_SIZE", "50")
    
    settings = Settings()
    
    assert settings.api_port == 9000
    assert settings.log_level == "DEBUG"
    assert settings.max_batch_size == 50


def test_get_settings():
    """Test get_settings function."""
    settings = get_settings()
    assert isinstance(settings, Settings)


def test_ensure_directories(tmp_path):
    """Test directory creation."""
    # Create test settings with temp paths
    test_settings = Settings(
        upload_dir=str(tmp_path / "uploads"),
        processed_dir=str(tmp_path / "processed"),
        temp_dir=str(tmp_path / "temp"),
        log_file=str(tmp_path / "logs" / "test.log"),
        model_path=str(tmp_path / "models")
    )
    
    # Mock global settings
    import config
    original_settings = config.settings
    config.settings = test_settings
    
    try:
        ensure_directories()
        
        # Verify directories were created
        assert Path(test_settings.upload_dir).exists()
        assert Path(test_settings.processed_dir).exists()
        assert Path(test_settings.temp_dir).exists()
        assert Path(test_settings.log_file).parent.exists()
        assert Path(test_settings.model_path).exists()
    finally:
        # Restore original settings
        config.settings = original_settings
