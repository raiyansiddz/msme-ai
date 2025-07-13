"""
Configuration management for the MSME SaaS platform
"""
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Settings:
    """Application settings"""
    
    def __init__(self):
        # Database settings
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.environ.get('DB_NAME', 'msme_saas')
        
        # JWT settings
        self.jwt_secret_key = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = 30
        
        # AI settings
        self.gemini_api_key = os.environ.get('GEMINI_API_KEY', '')
        
        # Email settings
        self.smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_user = os.environ.get('SMTP_USER', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        
        # WhatsApp settings
        self.whatsapp_token = os.environ.get('WHATSAPP_TOKEN', '')
        self.whatsapp_phone_number_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')
        
        # Application settings
        self.app_name = "MSME SaaS Platform"
        self.app_version = "1.0.0"
        self.debug = os.environ.get('DEBUG', 'false').lower() == 'true'

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