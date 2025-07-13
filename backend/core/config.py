"""
Configuration management for the MSME SaaS platform
"""
import os
from typing import Optional
from pydantic import BaseSettings
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings"""
    
    # Database settings
    mongo_url: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name: str = os.environ.get('DB_NAME', 'msme_saas')
    
    # JWT settings
    jwt_secret_key: str = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # AI settings
    gemini_api_key: str = os.environ.get('GEMINI_API_KEY', '')
    
    # Email settings
    smtp_host: str = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port: int = int(os.environ.get('SMTP_PORT', '587'))
    smtp_user: str = os.environ.get('SMTP_USER', '')
    smtp_password: str = os.environ.get('SMTP_PASSWORD', '')
    
    # WhatsApp settings
    whatsapp_token: str = os.environ.get('WHATSAPP_TOKEN', '')
    whatsapp_phone_number_id: str = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')
    
    # Application settings
    app_name: str = "MSME SaaS Platform"
    app_version: str = "1.0.0"
    debug: bool = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings"""
    return settings

# Logging configuration
def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO if not settings.debug else logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    logger.info("Logging configuration completed")