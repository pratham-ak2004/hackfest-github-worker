from . import BaseEventTask

class TestTask(BaseEventTask):
    name = "test_task"
    
    def process(self, event: dict) -> dict:
        self.logger.debug(f"Processing event in {self.name}: {event}")
        return {"status": "success", "processed_event": event}