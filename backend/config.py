from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    api_version: str = "v1"
    api_title: str = "Bank Statement Reconciliation API"
    api_description: str = "AI-powered middleware for Nigerian bank statement reconciliation"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    api_key_header: str = "X-API-Key"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    allowed_hosts: str = "*"
    
    # File Upload Settings
    max_upload_size: int = 52428800  # 50MB
    max_batch_size: int = 100
    upload_dir: str = "./uploads"
    processed_dir: str = "./processed"
    temp_dir: str = "./temp"
    retention_days: int = 7
    
    # DocuClipper Integration
    docuclipper_api_url: str = "https://api.docuclipper.com/v1"
    docuclipper_api_key: str = ""
    docuclipper_timeout: int = 30
    
    # Database
    database_url: str = "sqlite:///./bankstate.db"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = "./logs/bankstate.log"
    
    # Processing
    async_processing: bool = False
    worker_timeout: int = 300
    max_retries: int = 3
    
    # AI Model
    model_path: str = "./models"
    hf_model_name: str = "microsoft/layoutlm-base-uncased"
    use_gpu: bool = False
    
    # Monitoring
    enable_metrics: bool = True
    health_check_interval: int = 60
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings


def ensure_directories():
    """Ensure required directories exist."""
    directories = [
        settings.upload_dir,
        settings.processed_dir,
        settings.temp_dir,
        os.path.dirname(settings.log_file),
        settings.model_path,
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
