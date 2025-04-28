"""
Configuration module for the AccountDB application.

This module loads environment variables and provides a centralized configuration
for the application. It includes validation to ensure required variables are set.
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

class Config:
    """Application configuration."""

    # Database configuration
    DB_HOST: str = os.getenv('PG_HOST', 'localhost')
    DB_PORT: str = os.getenv('PG_PORT', '5432')
    DB_NAME: str = os.getenv('DB_NAME', 'accountdb')
    DB_USER: str = os.getenv('PG_USER', 'postgres')
    DB_PASS: str = os.getenv('PG_PASSWORD')

    # JWT configuration
    JWT_SECRET: str = os.getenv('JWT_SECRET_KEY')
    JWT_ALGORITHM: str = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '1440'))

    # API configuration
    API_HOST: str = os.getenv('API_HOST', '0.0.0.0')
    API_PORT: int = int(os.getenv('API_PORT', '8080'))
    API_TOKEN: str = os.getenv('API_TOKEN')
    X_TOKEN: str = os.getenv('X_TOKEN')

    # CORS configuration
    CORS_ORIGINS: list = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:8084').split(',')

    # Registration settings
    SIGNUPS_ENABLED: bool = os.getenv('SIGNUPS_ENABLED', 'true').lower() == 'true'

    # Logging configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    LOG_FILE: str = os.getenv('LOG_FILE', 'logs/app.log')
    LOG_ROTATION: bool = os.getenv('LOG_ROTATION', 'true').lower() == 'true'
    LOG_MAX_SIZE: int = int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10 MB
    LOG_BACKUP_COUNT: int = int(os.getenv('LOG_BACKUP_COUNT', '5'))

    # Error handling configuration
    ERROR_REPORTING_ENABLED: bool = os.getenv('ERROR_REPORTING_ENABLED', 'false').lower() == 'true'
    SENTRY_DSN: Optional[str] = os.getenv('SENTRY_DSN')
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv('SLACK_WEBHOOK_URL')
    ERROR_EMAIL_TO: Optional[str] = os.getenv('ERROR_EMAIL_TO')
    ERROR_EMAIL_FROM: str = os.getenv('ERROR_EMAIL_FROM', 'errors@accountdb.app')
    ERROR_RATE_LIMIT: int = int(os.getenv('ERROR_RATE_LIMIT', '60'))  # 1 per minute
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')

    # SMTP configuration for error reporting
    SMTP_HOST: str = os.getenv('SMTP_HOST', 'localhost')
    SMTP_PORT: int = int(os.getenv('SMTP_PORT', '25'))
    SMTP_USERNAME: Optional[str] = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD: Optional[str] = os.getenv('SMTP_PASSWORD')
    SMTP_USE_TLS: bool = os.getenv('SMTP_USE_TLS', 'false').lower() == 'true'

    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """
        Validate the configuration.

        Returns:
            Dict[str, Any]: A dictionary of validation errors or an empty dictionary if valid
        """
        errors = {}

        # Check required values
        if not cls.DB_PASS:
            errors['PG_PASSWORD'] = 'Database password is required'

        if not cls.JWT_SECRET:
            errors['JWT_SECRET_KEY'] = 'JWT secret is required'

        if not cls.API_TOKEN:
            errors['API_TOKEN'] = 'API token is required'

        if not cls.X_TOKEN:
            errors['X_TOKEN'] = 'X token is required'

        return errors

    @classmethod
    def is_valid(cls) -> bool:
        """
        Check if the configuration is valid.

        Returns:
            bool: True if the configuration is valid, False otherwise
        """
        return len(cls.validate()) == 0

    @classmethod
    def get(cls, key, default=None):
        """
        Get a configuration value by key, with a default value if not found.

        Args:
            key (str): The configuration key to get
            default: The default value to return if the key is not found

        Returns:
            The configuration value or the default value
        """
        return getattr(cls, key, default)

    @classmethod
    def log_config(cls) -> None:
        """
        Log the configuration (with sensitive values masked).
        """
        logger.info("Application configuration:")
        logger.info(f"  DB_HOST: {cls.DB_HOST}")
        logger.info(f"  DB_PORT: {cls.DB_PORT}")
        logger.info(f"  DB_NAME: {cls.DB_NAME}")
        logger.info(f"  DB_USER: {cls.DB_USER}")
        logger.info(f"  DB_PASS: {'*' * 8 if cls.DB_PASS else 'Not set'}")
        logger.info(f"  JWT_SECRET: {'*' * 8 if cls.JWT_SECRET else 'Not set'}")
        logger.info(f"  JWT_ALGORITHM: {cls.JWT_ALGORITHM}")
        logger.info(f"  JWT_EXPIRATION: {cls.JWT_EXPIRATION}")
        logger.info(f"  API_HOST: {cls.API_HOST}")
        logger.info(f"  API_PORT: {cls.API_PORT}")
        logger.info(f"  API_TOKEN: {'*' * 8 if cls.API_TOKEN else 'Not set'}")
        logger.info(f"  X_TOKEN: {'*' * 8 if cls.X_TOKEN else 'Not set'}")
        logger.info(f"  CORS_ORIGINS: {cls.CORS_ORIGINS}")
        logger.info(f"  SIGNUPS_ENABLED: {cls.SIGNUPS_ENABLED}")
        logger.info(f"  LOG_LEVEL: {cls.LOG_LEVEL}")
        logger.info(f"  ERROR_REPORTING_ENABLED: {cls.ERROR_REPORTING_ENABLED}")
        logger.info(f"  ENVIRONMENT: {cls.ENVIRONMENT}")

        # Log error reporting configuration if enabled
        if cls.ERROR_REPORTING_ENABLED:
            logger.info("Error reporting configuration:")
            logger.info(f"  SENTRY_DSN: {'Set' if cls.SENTRY_DSN else 'Not set'}")
            logger.info(f"  SLACK_WEBHOOK_URL: {'Set' if cls.SLACK_WEBHOOK_URL else 'Not set'}")
            logger.info(f"  ERROR_EMAIL_TO: {cls.ERROR_EMAIL_TO or 'Not set'}")
            logger.info(f"  ERROR_RATE_LIMIT: {cls.ERROR_RATE_LIMIT} seconds")

# Validate configuration on module import
config_errors = Config.validate()
if config_errors:
    for key, error in config_errors.items():
        logger.warning(f"Configuration error: {key} - {error}")
else:
    logger.info("Configuration validated successfully")
