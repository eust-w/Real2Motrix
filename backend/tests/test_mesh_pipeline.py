import builtins
from pathlib import Path
import json

import numpy as np
import trimesh

from app.pipeline.full_pipeline import run_mesh_pipeline
from app.pipeline.mesh import scene_split


def test_mesh_pipeline_exports_valid_motrix_package(tmp_path: Path) -> None:
    source_mesh = tmp_path / "source.obj"
    visual = trimesh.creation.icosphere(subdivisions=2, radius=0.4)
    visual.apply_translation((2.0, -3.0, 0.8))
    visual.export(source_mesh)

    result = run_mesh_pipeline(
        source_mesh=source_mesh,
        project_id="project-1",
        output_root=tmp_path / "outputs",
        source_info={"source_type": "mesh", "filename": source_mesh.name},
    )

    assert result.package_dir.name == "motrix_scene"
    assert (result.package_dir / "scene.xml").exists()
    assert (result.package_dir / "scene.urdf").exists()
    assert (result.package_dir / "scene.json").exists()
    assert (result.package_dir / "meshes" / "scene_visual.obj").exists()
    assert (result.package_dir / "meshes" / "scene_collision.obj").exists()
    assert result.validation_report["valid"] is True
    assert result.package_zip.exists()


def test_mesh_pipeline_exports_separate_scene_and_object_assets(tmp_path: Path) -> None:
    source_mesh = tmp_path / "source_with_object.obj"
    scene = trimesh.creation.icosphere(subdivisions=2, radius=1.5)
    scene.apply_translation((0.0, 0.0, 1.5))
    object_mesh = trimesh.creation.icosphere(subdivisions=2, radius=0.35)
    object_mesh.apply_translation((2.4, 0.0, 0.35))
    visual = trimesh.util.concatenate([scene, object_mesh])
    visual.export(source_mesh)

    result = run_mesh_pipeline(
        source_mesh=source_mesh,
        project_id="project-objects",
        output_root=tmp_path / "outputs",
        source_info={"source_type": "mesh", "filename": source_mesh.name},
    )

    package_dir = result.package_dir
    asset_manifest = json.loads((package_dir / "metadata" / "asset_manifest.json").read_text(encoding="utf-8"))
    object_manifest = json.loads((package_dir / "metadata" / "object_manifest.json").read_text(encoding="utf-8"))
    scene_xml = (package_dir / "scene.xml").read_text(encoding="utf-8")
    scene_urdf = (package_dir / "scene.urdf").read_text(encoding="utf-8")

    assert (package_dir / "metadata" / "scene_manifest.json").exists()
    assert asset_manifest["scene"]["visual_mesh"] == "meshes/scene_visual.obj"
    assert asset_manifest["scene"]["collision_mesh"] == "meshes/scene_collision.obj"
    assert len(asset_manifest["objects"]) == 1
    assert object_manifest["objects"][0]["id"] == "object_001"
    assert object_manifest["objects"][0]["visual_mesh"] == "meshes/objects/object_001/visual.obj"
    assert object_manifest["objects"][0]["collision_mesh"] == "meshes/objects/object_001/collision.obj"
    assert (package_dir / "meshes" / "objects" / "object_001" / "visual.obj").exists()
    assert (package_dir / "meshes" / "objects" / "object_001" / "collision.obj").exists()
    assert 'file="objects/object_001/visual.obj"' in scene_xml
    assert 'name="object_001"' in scene_xml
    assert 'filename="meshes/objects/object_001/visual.obj"' in scene_urdf
    assert result.validation_report["summary"]["object_count"] == 1


def test_scene_split_skips_dbscan_for_large_single_component_mesh(monkeypatch) -> None:
    vertices = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    faces = np.tile(np.array([[0, 1, 2], [0, 1, 3]]), (800, 1))
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    monkeypatch.setattr(scene_split, "_split_components", lambda visual_mesh: [visual_mesh.copy()])
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "sklearn.cluster":
            raise AssertionError("large single-component meshes should not run DBSCAN")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    result = scene_split.split_scene_objects(mesh, max_cluster_faces=100)

    assert result.segmentation["method"] == "connected_components"
    assert result.segmentation["object_count"] == 0
