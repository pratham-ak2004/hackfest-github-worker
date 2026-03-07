import os

from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from typing import Any
from utils.dashboard import DatabaseManager, QueryManager, SyncManager
from psycopg2.extras import RealDictCursor

class DashboardServer:
    def __init__(self):
        self.app = FastAPI(
            title="Hackfest Celery Dashboard",
            description="A dashboard to monitor Celery task processing and sync status",
            version="1.0.0",
        )
        
        self.templates = Jinja2Templates(
            directory=os.path.join(os.path.dirname(__file__), "../templates")
        )
        self.db_manager = DatabaseManager()
        self.query_manager = QueryManager(db_manager=self.db_manager)
        self.sync_manager = SyncManager(
            db_manager=self.db_manager, 
            query_manager=self.query_manager
            )
        
        self.app.get("/")(self.dashboard_page)
        self.app.get("/favicon.ico")(self.favicon)
        self.app.get("/api/health")(self.health)
        self.app.get("/api/stats")(self.get_stats)
        self.app.get("/api/tasks")(self.list_tasks)
        self.app.get("/api/tasks/{task_id}")(self.get_task)
        self.app.get("/api/sync/status")(self.get_sync_status)
        self.app.post("/api/sync/start")(self.start_sync_loop)
        self.app.post("/api/sync/stop")(self.stop_sync_loop)
        self.app.patch("/api/sync/config")(self.update_sync_config)
        
    async def favicon(self):
        return FileResponse(os.path.join(os.path.dirname(__file__), "../templates/dashboard/favicon.ico"))

    async def dashboard_page(self, request: Request):
        """Render the main dashboard page"""
        return self.templates.TemplateResponse(
            request=request,
            name="dashboard/index.html",
            context={}
            )
    
    async def health(self) -> dict[str, Any]:
        response = {
            "service": "hackfest-celery-dashboard",
            "time": datetime.now(timezone.utc).isoformat(),
            "database": "unknown",
            }
        try:
            with self.db_manager.get_db() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            response["database"] = "up"
        except Exception as exc:
            response["database"] = f"down: {exc}"
        return response
    
    async def get_stats(self) -> dict[str, Any]:
        try:
            return await self.query_manager.query_stats()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    async def list_tasks(
        self,
        status: str | None = Query(default=None),
        task_name: str | None = Query(default=None),
        task_id_contains: str | None = Query(default=None),
        limit: int = Query(default=50, ge=10, le=500),
        offset: int = Query(default=0, ge=0),
        ) -> dict[str, Any]:
        try:
            return await self.query_manager.query_tasks(
                status=status,
                task_name=task_name,
                task_id_contains=task_id_contains,
                limit=limit,
                offset=offset,
                )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    async def get_task(self, task_id: str) -> dict[str, Any]:
        try:
            with self.db_manager.get_db() as connection:
                with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        """
                        SELECT
                            id, task_id, status, result, date_done, traceback, name, args, kwargs, worker, retries, queue
                        FROM celery_taskmeta
                        WHERE task_id = %s
                        LIMIT 1
                        """,
                        (task_id,),
                        )
                    
                    row = cursor.fetchone()
                    
                    if not row:
                        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
                    return self.db_manager.row_to_task(dict(row))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
        
    async def get_sync_status(self) -> dict[str, Any]:
        """Get current sync status and statistics"""
        return {
            "running": self.sync_manager.sync_state["running"],
            "last_sync": self.sync_manager.sync_state["last_sync"],
            "synced_count": self.sync_manager.sync_state["synced_count"],
            "last_processed_id": self.sync_manager.sync_state["last_processed_id"],
            "poll_interval": self.sync_manager.sync_state["poll_interval"],
            "recent_errors": self.sync_manager.sync_state["errors"][-5:] if self.sync_manager.sync_state["errors"] else [],
            "total_errors": len(self.sync_manager.sync_state["errors"]),
            }
        
    async def start_sync_loop(self):
        """Start the background sync loop"""
        if self.sync_manager.sync_state["running"]:
            return {"status": "already_running", "message": "Sync is already running"}
        
        await self.sync_manager.start_sync_loop()
        return {"status": "started", "message": "Sync loop started successfully"}
    
    async def stop_sync_loop(self):
        """Stop the background sync loop"""
        if not self.sync_manager.sync_state["running"]:
            return {"status": "not_running", "message": "Sync is not currently running"}
        
        await self.sync_manager.stop_sync_loop()
        return {"status": "stopped", "message": "Sync loop stopped successfully"}
    
    async def update_sync_config(self, poll_interval: int = Query(ge=5, le=300)) -> dict[str, Any]:
        """Update sync configuration (e.g., poll interval)"""
        self.sync_manager.sync_state["poll_interval"] = poll_interval
        return {"status": "updated", "poll_interval": poll_interval}


server = DashboardServer()