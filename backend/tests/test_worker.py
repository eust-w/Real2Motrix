from pathlib import Path

import trimesh

from app.database import Database
from app.services.asset_service import list_assets
from app.services.job_service import create_job, get_job
from app.services.project_service import create_project
from app.worker import run_worker_once


def test_worker_registers_scene_and_object_assets_from_manifest(tmp_path: Path) -> None:
    db = Database(tmp_path / "real2motrix.sqlite3")
    project = create_project(db, tmp_path / "data", "Scene split", "", "mesh")
    source_mesh = tmp_path / "source.obj"
    scene = trimesh.creation.icosphere(subdivisions=2, radius=1.5)
    scene.apply_translation((0.0, 0.0, 1.5))
    object_mesh = trimesh.creation.icosphere(subdivisions=2, radius=0.35)
    object_mesh.apply_translation((2.4, 0.0, 0.35))
    trimesh.util.concatenate([scene, object_mesh]).export(source_mesh)
    job = create_job(db, project["id"], "mesh", source_mesh)

    assert run_worker_once(db, tmp_path / "outputs") is True

    completed = get_job(db, job["id"])
    assets = list_assets(db, project["id"])
    asset_types = {asset["asset_type"] for asset in assets}
    object_visual = next(asset for asset in assets if asset["asset_type"] == "object_visual_mesh")

    assert completed["status"] == "completed"
    assert {
        "motrix_package",
        "visual_mesh",
        "collision_mesh",
        "scene_visual_mesh",
        "scene_collision_mesh",
        "object_visual_mesh",
        "object_collision_mesh",
    }.issubset(asset_types)
    assert object_visual["metadata_json"]["object_id"] == "object_001"
    assert object_visual["metadata_json"]["visual_mesh"].endswith("objects/object_001/visual.obj")
