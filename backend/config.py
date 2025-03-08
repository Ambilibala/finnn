import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret')
    DATA_DIR = os.getenv('DATA_DIR', 'static/data')
    FMP_API_KEY = os.getenv('FMP_API_KEY')
    FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30 days

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = False
    TESTING = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # Use more secure settings for production
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_CSRF_PROTECT = True

# Config dictionary based on environment
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Get current configuration
def get_config():
    """Get the current configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'default')
    return config.get(env, config['default'])