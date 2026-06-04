import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List
from xml.sax.saxutils import escape


def write_scene_files(package_dir: Path, manifest: Dict[str, Any], source_info: Dict[str, Any]) -> None:
    metadata_dir = package_dir / "metadata"
    raw_dir = package_dir / "raw"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    scene = _scene_manifest(manifest)
    objects = _object_manifests(manifest)

    (package_dir / "scene.xml").write_text(_build_mjcf(scene, objects), encoding="utf-8")
    (package_dir / "scene.urdf").write_text(_build_urdf(scene, objects), encoding="utf-8")
    (package_dir / "scene.json").write_text(
        json.dumps(_build_scene_index(scene, objects), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (metadata_dir / "asset_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (metadata_dir / "scene_manifest.json").write_text(
        json.dumps(scene, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (metadata_dir / "object_manifest.json").write_text(
        json.dumps(
            {
                "objects": objects,
                "count": len(objects),
                "segmentation": manifest.get("segmentation", {}),
                "coordinate_system": manifest.get("coordinate_system", "motrix_world"),
                "unit": manifest.get("unit", "meter"),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (metadata_dir / "semantic.json").write_text(
        json.dumps(
            {
                "labels": [
                    {
                        "id": item["id"],
                        "label": "object_candidate",
                        "source": item.get("source", "geometry"),
                    }
                    for item in objects
                ],
                "coordinate_system": manifest.get("coordinate_system", "motrix_world"),
                "unit": manifest.get("unit", "meter"),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (raw_dir / "source_info.json").write_text(
        json.dumps(source_info, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (package_dir / "README.md").write_text(_readme(), encoding="utf-8")


def _build_mjcf(scene: Dict[str, Any], objects: List[Dict[str, Any]]) -> str:
    asset_lines = [
        f'    <mesh name="scene_visual" file="{_xml_attr(_meshdir_file(scene["visual_mesh"]))}"/>',
        f'    <mesh name="scene_collision" file="{_xml_attr(_meshdir_file(scene["collision_mesh"]))}"/>',
    ]
    body_lines = [
        '    <body name="static_scene" pos="0 0 0">',
        '      <geom name="scene_collision_geom"',
        '            type="mesh"',
        '            mesh="scene_collision"',
        '            contype="1"',
        '            conaffinity="1"',
        '            friction="0.8 0.1 0.1"/>',
        '      <geom name="scene_visual_geom"',
        '            type="mesh"',
        '            mesh="scene_visual"',
        '            contype="0"',
        '            conaffinity="0"',
        '            rgba="1 1 1 1"/>',
        "    </body>",
    ]
    for item in objects:
        object_id = _safe_id(item["id"])
        visual_name = f"{object_id}_visual"
        collision_name = f"{object_id}_collision"
        asset_lines.extend(
            [
                f'    <mesh name="{_xml_attr(visual_name)}" file="{_xml_attr(_meshdir_file(item["visual_mesh"]))}"/>',
                f'    <mesh name="{_xml_attr(collision_name)}" file="{_xml_attr(_meshdir_file(item["collision_mesh"]))}"/>',
            ]
        )
        body_lines.extend(
            [
                f'    <body name="{_xml_attr(object_id)}" pos="0 0 0">',
                f'      <geom name="{_xml_attr(object_id)}_collision_geom"',
                '            type="mesh"',
                f'            mesh="{_xml_attr(collision_name)}"',
                '            contype="1"',
                '            conaffinity="1"',
                '            friction="0.8 0.1 0.1"/>',
                f'      <geom name="{_xml_attr(object_id)}_visual_geom"',
                '            type="mesh"',
                f'            mesh="{_xml_attr(visual_name)}"',
                '            contype="0"',
                '            conaffinity="0"',
                '            rgba="0.78 0.86 0.95 1"/>',
                "    </body>",
            ]
        )
    return "\n".join(
        [
            '<mujoco model="scanned_scene">',
            '  <compiler angle="radian" meshdir="meshes"/>',
            '  <option timestep="0.002" gravity="0 0 -9.81"/>',
            "  <asset>",
            *asset_lines,
            "  </asset>",
            "  <worldbody>",
            *body_lines,
            "  </worldbody>",
            "</mujoco>",
            "",
        ]
    )


def _build_urdf(scene: Dict[str, Any], objects: List[Dict[str, Any]]) -> str:
    lines = [
        '<robot name="scanned_scene">',
        '  <link name="static_scene">',
        "    <visual>",
        "      <geometry>",
        f'        <mesh filename="{_xml_attr(scene["visual_mesh"])}"/>',
        "      </geometry>",
        "    </visual>",
        "    <collision>",
        "      <geometry>",
        f'        <mesh filename="{_xml_attr(scene["collision_mesh"])}"/>',
        "      </geometry>",
        "    </collision>",
        "  </link>",
    ]
    for item in objects:
        object_id = _safe_id(item["id"])
        lines.extend(
            [
                f'  <link name="{_xml_attr(object_id)}">',
                "    <visual>",
                "      <geometry>",
                f'        <mesh filename="{_xml_attr(item["visual_mesh"])}"/>',
                "      </geometry>",
                "    </visual>",
                "    <collision>",
                "      <geometry>",
                f'        <mesh filename="{_xml_attr(item["collision_mesh"])}"/>',
                "      </geometry>",
                "    </collision>",
                "  </link>",
                f'  <joint name="fixed_{_xml_attr(object_id)}" type="fixed">',
                '    <parent link="static_scene"/>',
                f'    <child link="{_xml_attr(object_id)}"/>',
                '    <origin xyz="0 0 0" rpy="0 0 0"/>',
                "  </joint>",
            ]
        )
    lines.append("</robot>")
    lines.append("")
    return "\n".join(lines)


def _build_scene_index(scene: Dict[str, Any], objects: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "name": "scanned_scene",
        "type": "motrix_scene_package",
        "entry": "scene.xml",
        "entries": {"mjcf": "scene.xml", "urdf": "scene.urdf"},
        "assets": {
            "visual_mesh": scene["visual_mesh"],
            "collision_mesh": scene["collision_mesh"],
            "scene_manifest": "metadata/scene_manifest.json",
            "object_manifest": "metadata/object_manifest.json",
            "objects": {
                item["id"]: {
                    "visual_mesh": item["visual_mesh"],
                    "collision_mesh": item["collision_mesh"],
                    "body": item.get("binding", {}).get("body", item["id"]),
                    "gaussian_splat": item.get("gaussian_splat"),
                }
                for item in objects
            },
        },
        "metadata": "metadata/asset_manifest.json",
    }


def _scene_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    scene = manifest.get("scene")
    if isinstance(scene, dict):
        return scene
    return {
        "id": "static_scene",
        "role": "environment",
        "visual_mesh": manifest.get("visual_mesh", "meshes/scene_visual.obj"),
        "collision_mesh": manifest.get("collision_mesh", "meshes/scene_collision.obj"),
        "visual_faces": manifest.get("visual_faces"),
        "collision_faces": manifest.get("collision_faces"),
        "bbox": manifest.get("bbox"),
        "binding": {"type": "static_world", "body": "static_scene"},
        "gaussian_splat": None,
    }


def _object_manifests(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    objects = manifest.get("objects", [])
    if not isinstance(objects, list):
        return []
    return [item for item in objects if isinstance(item, dict) and item.get("id") and item.get("visual_mesh") and item.get("collision_mesh")]


def _meshdir_file(value: str) -> str:
    posix = PurePosixPath(value)
    if posix.parts and posix.parts[0] == "meshes":
        return str(PurePosixPath(*posix.parts[1:]))
    return str(posix)


def _safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    return cleaned or "asset"


def _xml_attr(value: Any) -> str:
    return escape(str(value), {'"': "&quot;"})


def _readme() -> str:
    return """# Real2Motrix Package

This folder is a MotrixSim-compatible scene package generated by Real2Motrix.

Import steps:
1. Open MotrixSim Web Viewer.
2. Drag this entire `motrix_scene` folder into the viewer.
3. Load `scene.xml`, `scene.urdf`, or `scene.json`.

Package layout:
- `meshes/scene_visual.obj` and `meshes/scene_collision.obj` contain the static environment.
- `meshes/objects/*/visual.obj` and `meshes/objects/*/collision.obj` contain geometry-derived object candidates when separable components exist.
- `metadata/asset_manifest.json` is the authoritative manifest for scene/object assets.
- `metadata/object_manifest.json` lists object candidates and their Motrix body bindings.

Gaussian splat paths are left empty unless a real 3DGS reconstruction is provided by the pipeline.
All asset references are relative so the package remains portable after download.
"""
