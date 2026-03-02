from .base import BaseEventTask
from eventprocessor.celery_app import app
from tasks.pipeline.automate import register_automate_github_task

register_automate_github_task()

__all__ = ["BaseEventTask"]