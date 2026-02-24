from utils.logger import get_logger
from eventprocessor.celery_app import app

logger = get_logger(__name__)

logger.info("Starting in WORKER mode - will process tasks from queue")

def start_celery_worker():
    """Start Celery worker"""
    logger.info("Starting Celery worker...")
    argv = ['worker', '--loglevel=error']
    app.worker_main(argv)
    
def start_flower():
    """Start Flower monitoring tool"""
    logger.info("Starting Flower monitoring tool...")
    argv = ['flower', '--port=5555']
    app.start(argv)
    
if __name__ == "__main__":
    import sys
    if "--flower" in sys.argv:
        start_flower()
    else:
        start_celery_worker()