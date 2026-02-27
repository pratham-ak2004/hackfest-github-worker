import logging
import sys
from config import settings

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        formatted = super().format(record)
        
        if hasattr(record, 'levelname') and record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            levelname_colored = f"{color}{record.levelname}{self.RESET}"
            formatted = formatted.replace(record.levelname, levelname_colored, 1)
        
        return formatted

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance
    
    Args:
        - **name** string
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
        logger.setLevel(level)
        
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger
