import psycopg2
import json
import pickle
import asyncio
import requests, json
from datetime import datetime, timezone
from contextlib import contextmanager
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection as Connection
from typing import Any, Generator
from config import settings

from tasks.pipeline.stages.team import CreateTeamTask
from tasks.pipeline.stages.repo import CreateRepoTask
from utils.schema import TaskResponse, GithubTeam, GithubRepository, HttpMethod

class DatabaseManager:
    connection: Connection | None = None
    
    def __init__(self):
        if psycopg2 is None:
            raise ImportError("psycopg2 library is not installed. Please install it to use database features.")
        
        self.connection = self._get_connection()
        
    def _get_connection(self) -> Connection:
        if self.connection is None or self.connection.closed:
            connection = psycopg2.connect(
                host=settings.DB_HOST,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                port=settings.DB_PORT
            )
            self.connection = connection
        return self.connection
    
    def ping(self) -> bool:
        """Check if the database connection is alive"""
        try:
            with self.get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
                    return True
        except Exception as exc:
            print(f"Database ping failed: {exc}")
            return False
    
    @contextmanager
    def get_db(self) -> Generator[Connection, None, None]:
        """Context manager to get a database connection"""
        conn = self._get_connection()
        try:
            yield conn
        finally:
            pass
        
    def to_bytes(self, data: Any) -> bytes | None:
        """Convert data to bytes for storage in the database"""
        if data is None:
            return None
        if isinstance(data, memoryview):
            return data.tobytes()
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return data.encode("utf-8")
        raise ValueError("Unsupported data type for byte conversion")
    
    def safe_jsonable(self, data: Any) -> Any:
        """Convert data to a JSON-serializable format for storage in the database"""
        if data is None:
            return None
        if isinstance(data, (str, int, float, bool)):
            return data
        if isinstance(data, dict):
            return {key: self.safe_jsonable(value) for key, value in data.items()}
        if isinstance(data, (list, tuple, set)):
            return [self.safe_jsonable(item) for item in data]
        return str(data)
    
    def decode_payload(self, payload: Any) -> dict[str, Any]:
        """Decode a JSON-encoded payload from the database"""
        raw = self.to_bytes(payload)
        if not raw:
            return {"decoded": None, "format": "empty"}
        
        try:
            return {"decoded": self.safe_jsonable(json.loads(raw.decode("utf-8"))), "format": "json"}
        except Exception:
            pass   
        try:
            obj = pickle.loads(raw)
            return {"decoded": self.safe_jsonable(obj), "format": "pickle"}
        except Exception:
            pass
        try:
            return {"decoded": raw.decode("utf-8", errors="replace"), "format": "text"}
        except Exception:
            return {"decoded": str(raw), "format": "raw"}
        
    def row_to_task(self, row: dict[str, Any]) -> dict[str, Any]:
        """Convert a database row to a task dictionary with decoded payload"""
        args_decoded = self.decode_payload(row.get("args"))
        kwargs_decoded = self.decode_payload(row.get("kwargs"))
        result_decoded = self.decode_payload(row.get("result"))
        
        return {
            "id": row.get("id"),
            "task_id": row.get("task_id"),
            "status": row.get("status") or "UNKNOWN",
            "name": row.get("name") or "(untracked-name)",
            "worker": row.get("worker") or "-",
            "queue": row.get("queue") or "-",
            "retries": row.get("retries") or 0,
            "date_done": row.get("date_done").isoformat() if row.get("date_done") else None,
            "traceback": row.get("traceback"),
            "args": args_decoded,
            "kwargs": kwargs_decoded,
            "result": result_decoded,
            }
        
class QueryManager:
    def __init__(self, db_manager: DatabaseManager | None = None):
        if db_manager is None:
            db_manager = DatabaseManager()
        self.db_manager = db_manager
        
    async def query_stats(self) -> dict[str, Any]:
        """Query aggregated statistics about tasks"""
        with self.db_manager.get_db() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE status = 'SUCCESS') AS success,
                        COUNT(*) FILTER (WHERE status = 'FAILURE') AS failure,
                        COUNT(*) FILTER (WHERE status = 'PENDING') AS pending,
                        COUNT(*) FILTER (WHERE status = 'STARTED') AS started,
                        COUNT(*) FILTER (WHERE status = 'RETRY') AS retry
                    FROM celery_taskmeta
                    """
                    )
                summary = dict(cursor.fetchone() or {})
            
                cursor.execute(
                    """
                    SELECT COALESCE(name, '(untracked-name)') AS name, COUNT(*) AS count
                    FROM celery_taskmeta
                    GROUP BY name
                    ORDER BY count DESC, name ASC
                    LIMIT 10
                    """
                    )
                top_tasks = cursor.fetchall() or []
                
                cursor.execute(
                    """
                    SELECT COALESCE(status, 'UNKNOWN') AS status, COUNT(*) AS count
                    FROM celery_taskmeta
                    GROUP BY status
                    ORDER BY count DESC
                    """
                    )
                status_breakdown = cursor.fetchall() or []
                
            now = datetime.now(timezone.utc).isoformat()
            total = summary.get("total", 0) or 0
            success_rate = round(((summary.get("success", 0) or 0) / total) * 100, 2) if total else 0.0
            return {
                "summary": {
                    "total": total,
                    "success": summary.get("success", 0) or 0,
                    "failure": summary.get("failure", 0) or 0,
                    "pending": summary.get("pending", 0) or 0,
                    "started": summary.get("started", 0) or 0,
                    "retry": summary.get("retry", 0) or 0,
                    "success_rate": success_rate,
                    },
                "top_tasks": [dict(item) for item in top_tasks],
                "status_breakdown": [dict(item) for item in status_breakdown],
                "generated_at": now,
                }
        
    async def query_tasks(
        self,
        status: str | None,
        task_name: str | None,
        task_id_contains: str | None,
        limit: int,
        offset: int
        ) -> dict[str, Any]:
        """Query tasks with optional filters and pagination"""
        conditions: list[str] = []
        params: list[Any] = []
        
        if status:
            conditions.append("status = %s")
            params.append(status)
        if task_name:
            conditions.append("COALESCE(name, '') ILIKE %s")
            params.append(f"%{task_name}%")
        if task_id_contains:
            conditions.append("COALESCE(task_id, '') ILIKE %s")
            params.append(f"%{task_id_contains}%")
            
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        with self.db_manager.get_db() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    f"SELECT COUNT(*) AS total FROM celery_taskmeta {where_clause}",
                    tuple(params),
                    )
                total = int((cursor.fetchone() or {}).get("total", 0))
                
                cursor.execute(
                    f"""
                    SELECT
                        id, task_id, status, result, date_done, traceback, name, args, kwargs, worker, retries, queue
                    FROM celery_taskmeta
                    {where_clause}
                    ORDER BY date_done DESC NULLS LAST, id DESC
                    LIMIT %s OFFSET %s
                    """,
                    tuple([*params, limit, offset]),
                    )
                rows = cursor.fetchall() or []
                
                tasks = [self.db_manager.row_to_task(dict(row)) for row in rows]
                return {
                    "items": tasks,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    }
                
class SyncManager:
    sync_state = {
        "running": False,  # Sync is OFF by default
        "last_sync": None,
        "synced_count": 0,
        "last_processed_id": 0,
        "errors": [],
        "poll_interval": 15,  # seconds
    }
    row_limit = 10
    sync_task_handle = None
    
    def __init__(self, db_manager: DatabaseManager | None = None, query_manager: QueryManager | None = None):
        if db_manager is None:
            db_manager = DatabaseManager()
        if query_manager is None:
            query_manager = QueryManager(db_manager)
            
        self.db_manager = db_manager
        self.query_manager = query_manager
        
    async def _make_request(self, method: HttpMethod, route: str, payload: dict[str, Any]) -> requests.Response:
        route = route if route.startswith("/") else f"/{route}"
        headers = {
            "Content-Type": "application/json",
            "X-Hackfest-Secret": settings.HACKFEST_SECRET
        }
        response = requests.request(method, f"{settings.HACKFEST_URL}/api/dashboard/worker{route}", headers=headers, json=payload)
        
        print(response.text)
        return response
    
    async def save_github_team(self, data: CreateTeamTask.TaskPayload) -> None:
        payload = GithubTeam(**data.data.github_team.model_dump())
        response = await self._make_request(HttpMethod.PUT, "/team", payload={
            "team_id": data.data.team_id,
            "team_no": data.data.team_no,
            "github_team": payload.model_dump(),
        })
        response.raise_for_status()
        
    async def save_github_repo(self, data: CreateRepoTask.TaskPayload) -> None:
        payload = GithubRepository(**data.data.github_repo.model_dump())
        response = await self._make_request(HttpMethod.PUT, "/repo", payload={
            "team_id": data.data.team_id,
            "team_no": data.data.team_no,
            "github_repo": payload.model_dump(),
        })
        response.raise_for_status()

    async def sync_to_user_db(self, task_name: str, task_row: dict[str, Any], decoded_result: dict[str, Any]) -> bool:
        """
            Args:
                    task_row: Dict containing id, task_id, name, status, date_done, etc.
                    decoded_result: Dict with 'decoded' (the actual result) and 'format' (json/pickle/text)
        """
        task_response = TaskResponse(**decoded_result.get("decoded", {}))
        
        try:
            match task_name:
                case CreateTeamTask.name:
                    payload = CreateTeamTask.TaskPayload(**task_response.payload)
                    await self.save_github_team(payload)
                    return True

                case CreateRepoTask.name:
                    payload = CreateRepoTask.TaskPayload(**task_response.payload)
                    await self.save_github_repo(payload)
                    return True
                
                case _:
                    raise ValueError(f"No sync logic defined for task name: {task_name}")
                
        except Exception as exc:
            error_msg = f"Error syncing task {task_row.get('task_id')}: {exc}"
            self.sync_state["errors"].append(
                {"time": datetime.now(timezone.utc).isoformat(), "error": error_msg}
                )
            if len(self.sync_state["errors"]) > 20:
                self.sync_state["errors"] = self.sync_state["errors"][-20:]
            return False
    
    async def sync_completed_tasks_loop(self) -> None:
        """Background loop that periodically syncs completed tasks to user DB"""
        task_names = [CreateTeamTask.name, CreateRepoTask.name]
        
        while self.sync_state["running"]:
            print("Sync loop tick: checking for completed tasks to sync...")
            try:
                with self.db_manager.get_db() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        # Get tasks completed since last check
                        cursor.execute(
                            f"""
                            SELECT id, task_id, name, status, result, date_done
                            FROM celery_taskmeta
                            WHERE status = 'SUCCESS' AND sync_status = FALSE
                            ORDER BY date_done ASC, id ASC
                            LIMIT {self.row_limit}
                            """
                            )
                        
                        tasks = cursor.fetchall() or []
                        
                        for task in tasks:
                            try:
                                # Decode result and call user's sync function
                                result_decoded = self.db_manager.decode_payload(task["result"])
                                
                                # skip tasks that are not in our tracked list to avoid unnecessary sync attempts
                                if task["name"] not in task_names:
                                    cursor.execute(
                                        "UPDATE celery_taskmeta SET sync_status = TRUE WHERE id = %s",
                                        (task["id"],)
                                        )
                                    conn.commit()
                                    continue
                                
                                success = await self.sync_to_user_db(task["name"], dict(task), result_decoded)
                                success = False
                                if success:
                                    cursor.execute(
                                        "UPDATE celery_taskmeta SET sync_status = TRUE WHERE id = %s",
                                        (task["id"],)
                                        )
                                    conn.commit()
                                else:
                                    raise ValueError(f"Sync function returned False for task {task['task_id']}")
                                    
                                self.sync_state["last_processed_id"] = task["id"]
                                self.sync_state["synced_count"] += 1
                            except Exception as task_err:
                                error_msg = f"Task {task['task_id']}: {str(task_err)}"
                                self.sync_state["errors"].append(
                                    {"time": datetime.now(timezone.utc).isoformat(), "error": error_msg}
                                    )
                                # Keep only last 20 errors
                                if len(self.sync_state["errors"]) > 20:
                                    self.sync_state["errors"] = self.sync_state["errors"][-20:]
                                    self.sync_state["last_sync"] = datetime.now(timezone.utc).isoformat()
                                    
            except Exception as exc:
                self.sync_state["errors"].append(
                    {"time": datetime.now(timezone.utc).isoformat(), "error": f"Sync loop error: {exc}"}
                    )
                if len(self.sync_state["errors"]) > 20:
                    self.sync_state["errors"] = self.sync_state["errors"][-20:]  
                
            finally:
                # Wait before next poll
                await asyncio.sleep(self.sync_state["poll_interval"])
            
        self.sync_state["running"] = False  # Mark as stopped when loop exits
        
    async def start_sync_loop(self) -> asyncio.Task:
        if self.sync_task_handle:
            return self.sync_task_handle
        else:
            self.sync_state["running"] = True
            self.sync_task_handle = asyncio.create_task(self.sync_completed_tasks_loop())
            return self.sync_task_handle
        
    async def stop_sync_loop(self) -> None:
        if self.sync_task_handle:
            try:
                await asyncio.wait_for(self.sync_task_handle, timeout=5.0)
            except asyncio.TimeoutError:
                self.sync_task_handle.cancel()
            finally:
                self.sync_task_handle = None
                self.sync_state["running"] = False