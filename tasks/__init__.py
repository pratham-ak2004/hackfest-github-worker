from .base import BaseEventTask
from eventprocessor.celery_app import app
from tasks.pipeline.automate import AutomateGithubTask
from tasks.pipeline.stages import *

app.register_task(AutomateGithubTask())
app.register_task(CreateTeamTask())
app.register_task(CreateRepoTask())

__all__ = ["BaseEventTask"]