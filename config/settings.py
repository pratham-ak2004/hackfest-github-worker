import os
from dotenv import load_dotenv
from typing import Union

load_dotenv()

class EnvironmentError(Exception):
    """Custom exception for missing environment variables."""
    pass

class Settings:
    @staticmethod
    def get_env(key, default=Union[str, None], required=False) -> str:
        """
        Get environment variable with validation
        
        Args:
            - **key** string
            - **default** string
            - **required** Boolean
            
        Returns:
            The environment variable value or default
            
        Raises:
            EnvironmentError: If required=True and variable not found
        """
        value = os.getenv(key, default)
        if required and value is None:
            raise EnvironmentError(f"Missing required environment variable: {key}")
        return value
    
    
    RABBITMQ_HOST = get_env.__func__("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT = int(get_env.__func__("RABBITMQ_PORT", "5672"))
    RABBITMQ_PASSWORD = get_env.__func__("RABBITMQ_PASSWORD", "password")
    RABBITMQ_USERNAME = get_env.__func__("RABBITMQ_USERNAME", "guest")
    
    DB_USER = get_env.__func__("DB_USER", "postgres")
    DB_PASSWORD = get_env.__func__("DB_PASSWORD", "password")
    DB_HOST = get_env.__func__("DB_HOST", "localhost")
    DB_PORT = int(get_env.__func__("DB_PORT", "5432"))
    DB_NAME = get_env.__func__("DB_NAME", "postgres")
    
    DB_URL = get_env.__func__("DB_URL", f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    SMTP_HOST = get_env.__func__("SMTP_HOST", None, required=True)
    SMTP_PORT = int(get_env.__func__("SMTP_PORT", None, required=True))
    SMTP_USER = get_env.__func__("SMTP_USER", None, required=True)
    SMTP_PASSWORD = get_env.__func__("SMTP_PASSWORD", None, required=True)
    
    GITHUB_ORG_TOKEN = get_env.__func__("GITHUB_ORG_TOKEN", None, required=True)
    GITHUB_INVITE_TOKEN = get_env.__func__("GITHUB_INVITE_TOKEN", None, required=True)
    
    HACKFEST_SECRET = get_env.__func__("HACKFEST_SECRET",None, required=True)
    HACKFEST_URL = get_env.__func__("HACKFEST_URL", "https://hackfest.dev")
    DASHBOARD_HOST = get_env.__func__("DASHBOARD_HOST", "0.0.0.0")
    DASHBOARD_PORT = int(get_env.__func__("DASHBOARD_PORT", "8000"))
    
    APPLICATION_NAME = "hackfest-celery-worker"
    GITHUB_ORG = "hackfest-dev"
    LOG_LEVEL = get_env.__func__("LOG_LEVEL", "INFO")
    EVENT_QUEUE = "celery"
    
settings = Settings()