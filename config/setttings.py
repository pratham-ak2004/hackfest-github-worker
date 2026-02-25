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
    RABBITMQ_PASSWORD = get_env.__func__("RABBITMQ_PASSWORD", "guest")
    RABBITMQ_USERNAME = get_env.__func__("RABBITMQ_USERNAME", "guest")
    
    REDIS_HOST = get_env.__func__("REDIS_HOST", "localhost")
    REDIS_PORT = int(get_env.__func__("REDIS_PORT", "6379"))
    REDIS_PASSWORD = get_env.__func__("REDIS_PASSWORD", "000000")
    REDIS_DB = int(get_env.__func__("REDIS_DB", "0"))
    REDIS_USERNAME = get_env.__func__("REDIS_USERNAME", None)
    
    REDIS_URL = get_env.__func__("REDIS_URL", f"redis://{REDIS_USERNAME + ':' if REDIS_USERNAME else ''}{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
    
    HACKFEST_SECRET = get_env.__func__("HACKFEST_SECRET",None, required=True)
    GITHUB_ORG_TOKEN = get_env.__func__("GITHUB_ORG_TOKEN", None, required=True)
    GITHUB_INVITE_TOKEN = get_env.__func__("GITHUB_INVITE_TOKEN", None, required=True)
    
    APPLICATION_NAME = "hackfest-github"
    EVENT_QUEUE = "events"
    
settings = Settings()