import json
import os
import pickle
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates

try:
		import psycopg2
		from psycopg2.extras import RealDictCursor
except Exception:  # pragma: no cover
		psycopg2 = None
		RealDictCursor = None


load_dotenv()

app = FastAPI(
		title="Hackfest Celery Dashboard",
		description="Single-page dashboard for Celery task metadata and execution details",
		version="1.0.0",
)

templates = Jinja2Templates(
		directory=os.path.join(os.path.dirname(__file__), "templates")
)


def _db_config() -> dict[str, Any]:
		return {
				"host": os.getenv("DB_HOST", "localhost"),
				"port": int(os.getenv("DB_PORT", "5432")),
				"dbname": os.getenv("DB_NAME", "postgres"),
				"user": os.getenv("DB_USER", "postgres"),
				"password": os.getenv("DB_PASSWORD", "password"),
		}


@contextmanager
def _get_connection():
		if psycopg2 is None:
				raise RuntimeError(
						"Missing dependency: psycopg2-binary is required to query celery_taskmeta"
				)
		connection = psycopg2.connect(**_db_config())
		try:
				yield connection
		finally:
				connection.close()


def _to_bytes(data: Any) -> bytes | None:
		if data is None:
				return None
		if isinstance(data, memoryview):
				return data.tobytes()
		if isinstance(data, bytes):
				return data
		return str(data).encode("utf-8", errors="ignore")


def _safe_jsonable(value: Any) -> Any:
		if value is None:
				return None
		if isinstance(value, (str, int, float, bool)):
				return value
		if isinstance(value, dict):
				return {str(k): _safe_jsonable(v) for k, v in value.items()}
		if isinstance(value, (list, tuple, set)):
				return [_safe_jsonable(item) for item in value]
		return str(value)


def _decode_payload(data: Any) -> dict[str, Any]:
		raw = _to_bytes(data)
		if not raw:
				return {"decoded": None, "format": "empty"}

		try:
				return {"decoded": _safe_jsonable(json.loads(raw.decode("utf-8"))), "format": "json"}
		except Exception:
				pass

		try:
				obj = pickle.loads(raw)
				return {"decoded": _safe_jsonable(obj), "format": "pickle"}
		except Exception:
				pass

		try:
				return {"decoded": raw.decode("utf-8", errors="replace"), "format": "text"}
		except Exception:
				return {"decoded": str(raw), "format": "raw"}


def _row_to_task(row: dict[str, Any]) -> dict[str, Any]:
		args_decoded = _decode_payload(row.get("args"))
		kwargs_decoded = _decode_payload(row.get("kwargs"))
		result_decoded = _decode_payload(row.get("result"))

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


def _query_stats(connection) -> dict[str, Any]:
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


def _query_tasks(
		connection,
		status: str | None,
		task_name: str | None,
		task_id_contains: str | None,
		limit: int,
		offset: int,
) -> dict[str, Any]:
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

		with connection.cursor(cursor_factory=RealDictCursor) as cursor:
				cursor.execute(
						f"SELECT COUNT(*) AS total FROM celery_taskmeta {where_clause}",
						tuple(params),
				)
				total = int((cursor.fetchone() or {}).get("total", 0))

				cursor.execute(
						f"""
						SELECT
								id, task_id, status, result, date_done, traceback,
								name, args, kwargs, worker, retries, queue
						FROM celery_taskmeta
						{where_clause}
						ORDER BY date_done DESC NULLS LAST, id DESC
						LIMIT %s OFFSET %s
						""",
						tuple([*params, limit, offset]),
				)
				rows = cursor.fetchall() or []

		tasks = [_row_to_task(dict(row)) for row in rows]
		return {
				"items": tasks,
				"total": total,
				"limit": limit,
				"offset": offset,
		}


@app.get("/")
def dashboard_page(request: Request):
		return templates.TemplateResponse(
				request=request,
				name="dashboard/index.html",
				context={},
		)


@app.get("/api/health")
def health() -> dict[str, Any]:
		response = {
				"service": "hackfest-celery-dashboard",
				"time": datetime.now(timezone.utc).isoformat(),
				"database": "unknown",
		}
		try:
				with _get_connection() as connection:
						with connection.cursor() as cursor:
								cursor.execute("SELECT 1")
								cursor.fetchone()
				response["database"] = "up"
		except Exception as exc:
				response["database"] = f"down: {exc}"
		return response


@app.get("/api/stats")
def get_stats() -> dict[str, Any]:
		try:
				with _get_connection() as connection:
						return _query_stats(connection)
		except Exception as exc:
				raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/tasks")
def list_tasks(
		status: str | None = Query(default=None),
		task_name: str | None = Query(default=None),
		task_id_contains: str | None = Query(default=None),
		limit: int = Query(default=50, ge=10, le=500),
		offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
		try:
				with _get_connection() as connection:
						return _query_tasks(
								connection=connection,
								status=status,
								task_name=task_name,
								task_id_contains=task_id_contains,
								limit=limit,
								offset=offset,
						)
		except Exception as exc:
				raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str) -> dict[str, Any]:
		try:
				with _get_connection() as connection:
						with connection.cursor(cursor_factory=RealDictCursor) as cursor:
								cursor.execute(
										"""
										SELECT
												id, task_id, status, result, date_done, traceback,
												name, args, kwargs, worker, retries, queue
										FROM celery_taskmeta
										WHERE task_id = %s
										LIMIT 1
										""",
										(task_id,),
								)
								row = cursor.fetchone()

						if not row:
								raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
						return _row_to_task(dict(row))
		except HTTPException:
				raise
		except Exception as exc:
				raise HTTPException(status_code=500, detail=str(exc))
