from .base import BaseEventTask
from eventprocessor.celery_app import app

from .test import TestTask

app.register_task(TestTask())

__all__ = ["BaseEventTask"]