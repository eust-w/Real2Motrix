import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from app.database import Database
from app.pipeline.full_pipeline import run_full_pipeline
from app.services.asset_service import clear_project_assets, create_asset
from app.services.job_service import (
    add_job_log,
    get_job,
    mark_job_completed,
    mark_job_failed,
    mark_job_running,
    next_queued_job,
    update_job_progress,
)
from app.services.project_service import update_project_status
from app.settings import get_settings


def run_worker_once(db: Database, output_dir: Path) -> bool:
    job = next_queued_job(db)
    if not job:
        return False
    job_id = job["id"]
    project_id = job["project_id"]

    def log(level: str, message: str) -> None:
        add_job_log(db, job_id, level, message)

    try:
        mark_job_running(db, job_id)
        update_project_status(db, project_id, "running")
        log("info", f"started {job['source_type']} job")
        if not job["input_path"]:
            raise ValueError("job has no input_path; upload a source file or capture session first")
        update_job_progress(db, job_id, "pipeline", 10)
        params = job["params_json"] or {}
        result = run_full_pipeline(
            source_type=job["source_type"],
            input_path=Path(job["input_path"]),
            project_id=project_id,
            output_root=output_dir,
            log=log,
            fast_mode=bool(params.get("fast_mode")),
        )
        update_job_progress(db, job_id, "registering_assets", 95)
        clear_project_assets(db, project_id)
        manifest = _read_asset_manifest(result.package_dir)
        scene_manifest = manifest.get("scene", {}) if isinstance(manifest.get("scene"), dict) else {}
        scene_visual_mesh = scene_manifest.get("visual_mesh", "meshes/scene_visual.obj")
        scene_collision_mesh = scene_manifest.get("collision_mesh", "meshes/scene_collision.obj")
        create_asset(
            db,
            project_id,
            "motrix_package",
            result.package_zip,
            {"validation": result.validation_report},
        )
        create_asset(
            db,
            project_id,
            "visual_mesh",
            _package_path(result.package_dir, scene_visual_mesh),
            result.validation_report.get("summary", {}),
        )
        create_asset(
            db,
            project_id,
            "collision_mesh",
            _package_path(result.package_dir, scene_collision_mesh),
            result.validation_report.get("summary", {}),
        )
        create_asset(
            db,
            project_id,
            "scene_visual_mesh",
            _package_path(result.package_dir, scene_visual_mesh),
            _asset_metadata("scene_visual", scene_manifest, result.validation_report.get("summary", {})),
        )
        create_asset(
            db,
            project_id,
            "scene_collision_mesh",
            _package_path(result.package_dir, scene_collision_mesh),
            _asset_metadata("scene_collision", scene_manifest, result.validation_report.get("summary", {})),
        )
        for object_manifest in _object_manifests(manifest):
            create_asset(
                db,
                project_id,
                "object_visual_mesh",
                _package_path(result.package_dir, object_manifest.get("visual_mesh")),
                _asset_metadata("object_visual", object_manifest, {"object_id": object_manifest.get("id")}),
            )
            create_asset(
                db,
                project_id,
                "object_collision_mesh",
                _package_path(result.package_dir, object_manifest.get("collision_mesh")),
                _asset_metadata("object_collision", object_manifest, {"object_id": object_manifest.get("id")}),
            )
        mark_job_completed(db, job_id)
        update_project_status(db, project_id, "completed")
        log("info", "job completed")
        get_job(db, job_id)
        return True
    except Exception as exc:
        message = str(exc)
        log("error", message)
        mark_job_failed(db, job_id, message)
        update_project_status(db, project_id, "failed")
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Real2Motrix local worker process")
    parser.add_argument("--once", action="store_true", help="process one queued job then exit")
    args = parser.parse_args()
    settings = get_settings()
    db = Database(settings.database_path)
    while True:
        processed = run_worker_once(db, settings.output_dir)
        if args.once:
            return
        if not processed:
            time.sleep(settings.worker_poll_seconds)


def _read_asset_manifest(package_dir: Path) -> Dict[str, Any]:
    path = package_dir / "metadata" / "asset_manifest.json"
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _object_manifests(manifest: Dict[str, Any]):
    objects = manifest.get("objects", [])
    if not isinstance(objects, list):
        return []
    return [
        item
        for item in objects
        if isinstance(item, dict) and item.get("id") and item.get("visual_mesh") and item.get("collision_mesh")
    ]


def _package_path(package_dir: Path, relative_path: Optional[str]) -> Path:
    if not relative_path:
        return package_dir
    return package_dir / relative_path


def _asset_metadata(kind: str, manifest: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    metadata = dict(manifest)
    metadata.update(extra)
    metadata["kind"] = kind
    return metadata


if __name__ == "__main__":
    main()
