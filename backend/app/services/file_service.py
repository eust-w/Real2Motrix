import uuid
from pathlib import Path
from typing import Dict, List

from app.database import Database, utc_now


def create_uploaded_file(
    db: Database,
    project_id: str,
    filename: str,
    path: Path,
    file_type: str,
    size: int,
) -> Dict:
    file_id = str(uuid.uuid4())
    db.execute(
        """
        INSERT INTO uploaded_files (id, project_id, filename, path, file_type, size, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (file_id, project_id, filename, str(path), file_type, size, utc_now()),
    )
    return get_uploaded_file(db, file_id)


def get_uploaded_file(db: Database, file_id: str) -> Dict:
    record = db.fetch_one("SELECT * FROM uploaded_files WHERE id = ?", (file_id,))
    if not record:
        raise KeyError(file_id)
    return record


def list_uploaded_files(db: Database, project_id: str) -> List[Dict]:
    return db.fetch_all(
        "SELECT * FROM uploaded_files WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,),
    )

