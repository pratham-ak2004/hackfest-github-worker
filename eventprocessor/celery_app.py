from celery import Celery
from config import settings
from config import celery_config

app = Celery(settings.APPLICATION_NAME)
app.config_from_object(celery_config)

app.autodiscover_tasks(packages=["tasks"])