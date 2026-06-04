import uuid
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from app.database import Database, utc_now


def create_project(db: Database, data_dir: Path, name: str, description: str, source_type: str) -> Dict:
    project_id = str(uuid.uuid4())
    now = utc_now()
    root_dir = data_dir / project_id
    root_dir.mkdir(parents=True, exist_ok=True)
    db.execute(
        """
        INSERT INTO projects (id, name, description, source_type, status, root_dir, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (project_id, name, description, source_type, "created", str(root_dir), now, now),
    )
    return get_project(db, project_id)


def get_project(db: Database, project_id: str) -> Dict:
    project = db.fetch_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    if not project:
        raise KeyError(project_id)
    return project


def list_projects(db: Database) -> List[Dict]:
    return db.fetch_all("SELECT * FROM projects ORDER BY created_at DESC")


def delete_project(db: Database, project_id: str) -> None:
    project = get_project(db, project_id)
    db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    shutil.rmtree(project["root_dir"], ignore_errors=True)


def update_project_status(db: Database, project_id: str, status: str) -> None:
    db.execute(
        "UPDATE projects SET status = ?, updated_at = ? WHERE id = ?",
        (status, utc_now(), project_id),
    )


def sync_project_status_from_jobs(db: Database, project_id: str) -> None:
    rows = db.fetch_all(
        "SELECT status FROM jobs WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,),
    )
    if not rows:
        next_status = "created"
    elif any(row["status"] == "running" for row in rows):
        next_status = "running"
    elif any(row["status"] == "queued" for row in rows):
        next_status = "queued"
    else:
        next_status = rows[0]["status"]
    update_project_status(db, project_id, next_status)


def update_project(
    db: Database,
    project_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    source_type: Optional[str] = None,
) -> Dict:
    current = get_project(db, project_id)
    db.execute(
        """
        UPDATE projects
        SET name = ?, description = ?, source_type = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            name if name is not None else current["name"],
            description if description is not None else current["description"],
            source_type if source_type is not None else current["source_type"],
            utc_now(),
            project_id,
        ),
    )
    return get_project(db, project_id)
