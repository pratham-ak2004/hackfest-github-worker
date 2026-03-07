from utils.logger import get_logger
from eventprocessor.celery_app import app
from config import settings
import uvicorn, sys

logger = get_logger(__name__)

def start_celery_worker():
    """Start Celery worker"""
    logger.info("Starting Celery worker...")
    argv = ['worker', "--loglevel=info"]
    app.worker_main(argv)
    
def start_flower():
    """Start Flower monitoring tool"""
    logger.info("Starting Flower monitoring tool...")
    argv = ['flower', '--port=5555']
    app.start(argv)
    
def start_dashboard():
    """Start the FastAPI dashboard server"""
    logger.info("Starting FastAPI dashboard server...")
    uvicorn.run(
        "eventprocessor.fastapi:server.app", 
        host=settings.DASHBOARD_HOST, 
        port=settings.DASHBOARD_PORT, 
        log_level=settings.LOG_LEVEL.lower()
        )

if __name__ == "__main__":
    if "--flower" in sys.argv:
        start_flower()
    elif "--dashboard" in sys.argv:
        start_dashboard()
    else:
        start_celery_worker()