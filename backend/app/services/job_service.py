import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.database import Database, json_dumps, json_loads, utc_now


def create_job(
    db: Database,
    project_id: str,
    source_type: str,
    input_path: Optional[Path],
    capture_session_id: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict:
    job_id = str(uuid.uuid4())
    db.execute(
        """
        INSERT INTO jobs (
            id, project_id, capture_session_id, status, progress, current_step,
            error_message, source_type, input_path, params_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            project_id,
            capture_session_id,
            "queued",
            0,
            "queued",
            None,
            source_type,
            str(input_path) if input_path else None,
            json_dumps(params or {}),
            utc_now(),
        ),
    )
    return get_job(db, job_id)


def get_job(db: Database, job_id: str) -> Dict:
    job = db.fetch_one("SELECT * FROM jobs WHERE id = ?", (job_id,))
    if not job:
        raise KeyError(job_id)
    return normalize_job(job)


def list_jobs(db: Database, project_id: str) -> List[Dict]:
    return [
        normalize_job(row)
        for row in db.fetch_all(
            "SELECT * FROM jobs WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        )
    ]


def list_running_jobs(db: Database) -> List[Dict]:
    return [
        normalize_job(row)
        for row in db.fetch_all(
            "SELECT * FROM jobs WHERE status = 'running' ORDER BY started_at ASC, created_at ASC",
        )
    ]


def next_queued_job(db: Database) -> Optional[Dict]:
    row = db.fetch_one("SELECT * FROM jobs WHERE status = 'queued' ORDER BY created_at ASC LIMIT 1")
    return normalize_job(row) if row else None


def mark_job_running(db: Database, job_id: str) -> None:
    db.execute(
        "UPDATE jobs SET status = 'running', started_at = ?, current_step = ?, progress = ? WHERE id = ?",
        (utc_now(), "starting", 1, job_id),
    )


def update_job_progress(db: Database, job_id: str, step: str, progress: float) -> None:
    db.execute(
        "UPDATE jobs SET current_step = ?, progress = ? WHERE id = ?",
        (step, max(0, min(100, progress)), job_id),
    )


def mark_job_completed(db: Database, job_id: str) -> None:
    db.execute(
        "UPDATE jobs SET status = 'completed', progress = 100, current_step = 'completed', finished_at = ? WHERE id = ?",
        (utc_now(), job_id),
    )


def mark_job_failed(db: Database, job_id: str, message: str) -> None:
    db.execute(
        """
        UPDATE jobs
        SET status = 'failed', error_message = ?, current_step = 'failed', finished_at = ?
        WHERE id = ?
        """,
        (message, utc_now(), job_id),
    )


def add_job_log(db: Database, job_id: str, level: str, message: str) -> None:
    db.execute(
        "INSERT INTO job_logs (job_id, level, message, created_at) VALUES (?, ?, ?, ?)",
        (job_id, level, message, utc_now()),
    )


def list_job_logs(db: Database, job_id: str) -> List[Dict]:
    return db.fetch_all(
        "SELECT id, job_id, level, message, created_at FROM job_logs WHERE job_id = ? ORDER BY id ASC",
        (job_id,),
    )


def normalize_job(row: Dict) -> Dict:
    result = dict(row)
    result["params_json"] = json_loads(result["params_json"])
    return result
