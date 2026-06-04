import json
import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict

from app.database import Database, json_dumps, json_loads, utc_now


def read_capture_zip_metadata(zip_path: Path) -> Dict[str, Any]:
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        if "metadata.json" not in names:
            raise ValueError("capture_session.zip must contain metadata.json at the root")
        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        quality = {}
        if "quality/quality_report.json" in names:
            quality = json.loads(archive.read("quality/quality_report.json").decode("utf-8"))
    return {"metadata": metadata, "quality": quality}


def create_capture_session(
    db: Database,
    project_id: str,
    zip_path: Path,
    capture_type: str,
    capture_mode: str,
    device_model: str,
    has_lidar: bool,
) -> Dict:
    payload = read_capture_zip_metadata(zip_path)
    metadata = payload["metadata"]
    quality = payload["quality"]
    session_id = str(uuid.uuid4())
    db.execute(
        """
        INSERT INTO capture_sessions (
            id, project_id, capture_type, capture_mode, device_model, has_lidar,
            has_depth, has_arkit_pose, zip_path, metadata_json, quality_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            project_id,
            capture_type or metadata.get("capture_type", "scene"),
            capture_mode or metadata.get("capture_mode", "arkit_pose"),
            device_model or metadata.get("device_model", "unknown"),
            1 if has_lidar else 0,
            1 if metadata.get("has_depth") else 0,
            1 if metadata.get("has_arkit_pose", True) else 0,
            str(zip_path),
            json_dumps(metadata),
            json_dumps(quality),
            utc_now(),
        ),
    )
    return get_capture_session(db, session_id)


def get_capture_session(db: Database, session_id: str) -> Dict:
    record = db.fetch_one("SELECT * FROM capture_sessions WHERE id = ?", (session_id,))
    if not record:
        raise KeyError(session_id)
    return normalize_capture_session(record)


def list_capture_sessions(db: Database, project_id: str):
    rows = db.fetch_all(
        "SELECT * FROM capture_sessions WHERE project_id = ? ORDER BY created_at DESC",
        (project_id,),
    )
    return [normalize_capture_session(row) for row in rows]


def normalize_capture_session(row: Dict) -> Dict:
    result = dict(row)
    result["has_lidar"] = bool(result["has_lidar"])
    result["has_depth"] = bool(result["has_depth"])
    result["has_arkit_pose"] = bool(result["has_arkit_pose"])
    result["metadata_json"] = json_loads(result["metadata_json"])
    result["quality_json"] = json_loads(result["quality_json"])
    return result

