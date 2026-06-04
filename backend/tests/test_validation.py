import json
from pathlib import Path

import trimesh

from app.pipeline.motrix.validate import validate_package


def test_validation_rejects_absolute_mesh_references(tmp_path: Path) -> None:
    package_dir = tmp_path / "motrix_scene"
    (package_dir / "meshes").mkdir(parents=True)
    (package_dir / "metadata").mkdir()
    (package_dir / "scene.xml").write_text(
        """<mujoco model="bad"><asset><mesh name="bad" file="/tmp/bad.obj"/></asset></mujoco>""",
        encoding="utf-8",
    )
    (package_dir / "scene.urdf").write_text(
        """<robot name="bad"><link name="static_scene"><visual><geometry><mesh filename="meshes/visual.obj"/></geometry></visual></link></robot>""",
        encoding="utf-8",
    )
    (package_dir / "scene.json").write_text(
        json.dumps(
            {
                "name": "bad",
                "type": "motrix_scene_package",
                "entry": "scene.xml",
                "entries": {"mjcf": "scene.xml", "urdf": "scene.urdf"},
                "assets": {
                    "visual_mesh": "meshes/visual.obj",
                    "collision_mesh": "meshes/collision.obj",
                },
                "metadata": "metadata/asset_manifest.json",
            }
        ),
        encoding="utf-8",
    )
    (package_dir / "metadata" / "asset_manifest.json").write_text("{}", encoding="utf-8")

    report = validate_package(package_dir)

    assert report["valid"] is False
    assert any("absolute" in issue["message"] for issue in report["issues"])


def test_validation_accepts_portable_motrix_package(tmp_path: Path) -> None:
    package_dir = tmp_path / "motrix_scene"
    mesh_dir = package_dir / "meshes"
    metadata_dir = package_dir / "metadata"
    mesh_dir.mkdir(parents=True)
    metadata_dir.mkdir()

    visual = trimesh.creation.icosphere(subdivisions=2, radius=0.5)
    visual.apply_translation((0.0, 0.0, 0.5))
    collision = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    visual.export(mesh_dir / "scene_visual.obj")
    collision.export(mesh_dir / "scene_collision.obj")

    (package_dir / "scene.xml").write_text(
        """<mujoco model="scanned_scene"><compiler angle="radian" meshdir="meshes"/><asset><mesh name="scene_visual" file="scene_visual.obj"/><mesh name="scene_collision" file="scene_collision.obj"/></asset><worldbody><body name="static_scene" pos="0 0 0"><geom name="scene_collision_geom" type="mesh" mesh="scene_collision"/><geom name="scene_visual_geom" type="mesh" mesh="scene_visual" contype="0" conaffinity="0"/></body></worldbody></mujoco>""",
        encoding="utf-8",
    )
    (package_dir / "scene.urdf").write_text(
        """<robot name="scanned_scene"><link name="static_scene"><visual><geometry><mesh filename="meshes/scene_visual.obj"/></geometry></visual><collision><geometry><mesh filename="meshes/scene_collision.obj"/></geometry></collision></link></robot>""",
        encoding="utf-8",
    )
    (package_dir / "scene.json").write_text(
        json.dumps(
            {
                "name": "scanned_scene",
                "type": "motrix_scene_package",
                "entry": "scene.xml",
                "entries": {"mjcf": "scene.xml", "urdf": "scene.urdf"},
                "assets": {
                    "visual_mesh": "meshes/scene_visual.obj",
                    "collision_mesh": "meshes/scene_collision.obj",
                },
                "metadata": "metadata/asset_manifest.json",
            }
        ),
        encoding="utf-8",
    )
    (metadata_dir / "asset_manifest.json").write_text("{}", encoding="utf-8")

    report = validate_package(package_dir)

    assert report["valid"] is True
    assert report["summary"]["visual_faces"] > report["summary"]["collision_faces"]


def test_validation_accepts_collision_mesh_with_same_face_count_as_low_detail_visual(tmp_path: Path) -> None:
    package_dir = tmp_path / "motrix_scene"
    mesh_dir = package_dir / "meshes"
    metadata_dir = package_dir / "metadata"
    mesh_dir.mkdir(parents=True)
    metadata_dir.mkdir()

    visual = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
    visual.apply_translation((0.0, 0.0, 0.5))
    collision = visual.copy()
    visual.export(mesh_dir / "scene_visual.obj")
    collision.export(mesh_dir / "scene_collision.obj")

    (package_dir / "scene.xml").write_text(
        """<mujoco model="low_detail_scene"><compiler angle="radian" meshdir="meshes"/><asset><mesh name="scene_visual" file="scene_visual.obj"/><mesh name="scene_collision" file="scene_collision.obj"/></asset><worldbody><body name="static_scene" pos="0 0 0"><geom name="scene_collision_geom" type="mesh" mesh="scene_collision"/><geom name="scene_visual_geom" type="mesh" mesh="scene_visual" contype="0" conaffinity="0"/></body></worldbody></mujoco>""",
        encoding="utf-8",
    )
    (package_dir / "scene.urdf").write_text(
        """<robot name="low_detail_scene"><link name="static_scene"><visual><geometry><mesh filename="meshes/scene_visual.obj"/></geometry></visual><collision><geometry><mesh filename="meshes/scene_collision.obj"/></geometry></collision></link></robot>""",
        encoding="utf-8",
    )
    (package_dir / "scene.json").write_text(
        json.dumps(
            {
                "name": "low_detail_scene",
                "type": "motrix_scene_package",
                "entry": "scene.xml",
                "entries": {"mjcf": "scene.xml", "urdf": "scene.urdf"},
                "assets": {
                    "visual_mesh": "meshes/scene_visual.obj",
                    "collision_mesh": "meshes/scene_collision.obj",
                },
                "metadata": "metadata/asset_manifest.json",
            }
        ),
        encoding="utf-8",
    )
    (metadata_dir / "asset_manifest.json").write_text("{}", encoding="utf-8")

    report = validate_package(package_dir)

    assert report["valid"] is True
    assert report["summary"]["visual_faces"] == report["summary"]["collision_faces"]
