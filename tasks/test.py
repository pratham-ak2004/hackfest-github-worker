from . import BaseEventTask

class TestTask(BaseEventTask):
    name = "tasks.test.TestTask"
    
    def process(self, event: dict) -> dict:
        self.logger.info(f"Processing event in {self.name}: {event}")
        return {"status": "success", "processed_event": event}