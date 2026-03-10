from utils.logger import get_logger
from abc import ABC, abstractmethod
from celery import Task
from utils.schema import TaskResponse

lg = get_logger(__name__)

class BaseEventTask(Task, ABC):
    """Base class for event-based Celery tasks"""
    
    name = None
    max_retries = 5
    retry_countdown = 60
    
    def __init__(self, logger=lg):
        if not self.name:
            raise NotImplementedError("Subclasses must define name")
        super().__init__()
        self.logger = logger
        self.logger.debug(f"Initialized task: {self.name}")
    
    @abstractmethod
    def process(self, event: dict) -> TaskResponse:
        """Implement task logic here"""
        pass
    
    def run(self, event) -> dict:
        """Celery task entry point"""
        try:
            if not self.validate(event):
                self.logger.error(f"Invalid event data: {self.name} - {event}")
                raise ValueError("Invalid event data")
            
            result = self.process(event)
            self.logger.debug(f"Successfully processed {self.name}")
            return result
            
        except Exception as exc:
            self.logger.error(f"Error in {self.name}: {exc}")
            raise self.retry(exc=exc, countdown=self.retry_countdown)
    
    def validate(self, event: dict) -> bool:
        """Override for custom validation"""
        return isinstance(event, dict)