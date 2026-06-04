import uuid
from pathlib import Path
from typing import Any, Dict, List

from app.database import Database, json_dumps, json_loads, utc_now


def create_asset(
    db: Database,
    project_id: str,
    asset_type: str,
    path: Path,
    metadata: Dict[str, Any],
) -> Dict:
    asset_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO assets (id, project_id, asset_type, path, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (asset_id, project_id, asset_type, str(path), json_dumps(metadata), utc_now()),
    )
    return get_asset(db, asset_id)


def get_asset(db: Database, asset_id: str) -> Dict:
    asset = db.fetch_one("SELECT * FROM assets WHERE id = ?", (asset_id,))
    if not asset:
        raise KeyError(asset_id)
    return normalize_asset(asset)


def list_assets(db: Database, project_id: str) -> List[Dict]:
    return [
        normalize_asset(row)
        for row in db.fetch_all(
            "SELECT * FROM assets WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        )
    ]


def clear_project_assets(db: Database, project_id: str) -> None:
    db.execute("DELETE FROM assets WHERE project_id = ?", (project_id,))


def normalize_asset(row: Dict) -> Dict:
    result = dict(row)
    result["metadata_json"] = json_loads(result["metadata_json"])
    return result
