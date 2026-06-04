import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List

import trimesh


def validate_package(package_dir: Path) -> Dict[str, Any]:
    package_dir = Path(package_dir)
    issues: List[Dict[str, str]] = []
    summary: Dict[str, Any] = {}

    required = ["scene.xml", "scene.urdf", "scene.json", "metadata/asset_manifest.json"]
    for rel in required:
        if not (package_dir / rel).exists():
            issues.append({"level": "error", "message": f"missing required file: {rel}"})

    mjcf_root = _parse_xml(package_dir / "scene.xml", issues, "scene.xml")
    urdf_root = _parse_xml(package_dir / "scene.urdf", issues, "scene.urdf")
    scene_json = _parse_json(package_dir / "scene.json", issues, "scene.json")
    asset_manifest = _parse_json(package_dir / "metadata" / "asset_manifest.json", issues, "metadata/asset_manifest.json")

    mesh_refs: List[str] = []
    if mjcf_root is not None:
        meshdir = "meshes"
        compiler = mjcf_root.find("compiler")
        if compiler is not None and compiler.attrib.get("meshdir"):
            meshdir = compiler.attrib["meshdir"]
            _check_relative(meshdir, issues, "MJCF meshdir")
        for mesh in mjcf_root.findall(".//mesh"):
            ref = mesh.attrib.get("file")
            if ref:
                _check_relative(ref, issues, "MJCF mesh")
                mesh_refs.append(str(PurePosixPath(meshdir) / ref))
    if urdf_root is not None:
        for mesh in urdf_root.findall(".//mesh"):
            ref = mesh.attrib.get("filename") or mesh.attrib.get("file")
            if ref:
                _check_relative(ref, issues, "URDF mesh")
                mesh_refs.append(ref)
    if isinstance(scene_json, dict):
        for key in ("entry", "metadata"):
            value = scene_json.get(key)
            if isinstance(value, str):
                _check_relative(value, issues, f"scene.json {key}")
        assets = scene_json.get("assets", {})
        if isinstance(assets, dict):
            _collect_scene_asset_refs(assets, mesh_refs, issues, "scene.json assets")

    object_count = 0
    if isinstance(asset_manifest, dict):
        scene = asset_manifest.get("scene", {})
        if isinstance(scene, dict):
            for key in ("visual_mesh", "collision_mesh"):
                value = scene.get(key)
                if isinstance(value, str):
                    _check_relative(value, issues, f"asset_manifest scene {key}")
                    mesh_refs.append(value)
        objects = asset_manifest.get("objects", [])
        if isinstance(objects, list):
            object_count = len([item for item in objects if isinstance(item, dict)])
            for index, item in enumerate(objects):
                if not isinstance(item, dict):
                    continue
                for key in ("visual_mesh", "collision_mesh"):
                    value = item.get(key)
                    if isinstance(value, str):
                        _check_relative(value, issues, f"asset_manifest objects[{index}] {key}")
                        mesh_refs.append(value)
    summary["object_count"] = object_count

    loaded_meshes: Dict[str, trimesh.Trimesh] = {}
    for ref in sorted(set(mesh_refs)):
        candidate = _resolve_relative(package_dir, ref, issues)
        if candidate and candidate.exists():
            try:
                loaded = trimesh.load(candidate, force="mesh")
                if not isinstance(loaded, trimesh.Trimesh) or len(loaded.faces) == 0:
                    issues.append({"level": "error", "message": f"mesh is empty or unsupported: {ref}"})
                else:
                    loaded_meshes[ref] = loaded
            except Exception as exc:
                issues.append({"level": "error", "message": f"mesh cannot be loaded: {ref}: {exc}"})
        elif candidate:
            issues.append({"level": "error", "message": f"referenced mesh missing: {ref}"})

    visual = loaded_meshes.get("meshes/scene_visual.obj")
    collision = loaded_meshes.get("meshes/scene_collision.obj")
    if visual is not None:
        summary["visual_faces"] = int(len(visual.faces))
        summary["scene_visual_faces"] = int(len(visual.faces))
        bbox_issue = _bbox_issue(visual)
        if bbox_issue:
            issues.append({"level": "error", "message": bbox_issue})
    if collision is not None:
        summary["collision_faces"] = int(len(collision.faces))
        summary["scene_collision_faces"] = int(len(collision.faces))
    if visual is not None and collision is not None and len(collision.faces) >= len(visual.faces):
        issues.append(
            {
                "level": "error",
                "message": "collision mesh must have fewer faces than visual mesh",
            }
        )

    report = {
        "valid": not any(issue["level"] == "error" for issue in issues),
        "issues": issues,
        "summary": summary,
    }
    metadata_dir = package_dir / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    (metadata_dir / "validation_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return report


def _collect_scene_asset_refs(value: Any, mesh_refs: List[str], issues: List[Dict[str, str]], label: str) -> None:
    if isinstance(value, str):
        _check_relative(value, issues, label)
        if "mesh" in label:
            mesh_refs.append(value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            next_label = f"{label} {key}"
            if isinstance(item, str):
                _check_relative(item, issues, next_label)
                if "mesh" in key:
                    mesh_refs.append(item)
            elif isinstance(item, dict):
                _collect_scene_asset_refs(item, mesh_refs, issues, next_label)
            elif isinstance(item, list):
                for index, child in enumerate(item):
                    _collect_scene_asset_refs(child, mesh_refs, issues, f"{next_label}[{index}]")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _collect_scene_asset_refs(item, mesh_refs, issues, f"{label}[{index}]")


def _parse_xml(path: Path, issues: List[Dict[str, str]], label: str):
    if not path.exists():
        return None
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        issues.append({"level": "error", "message": f"{label} is not valid XML: {exc}"})
        return None


def _parse_json(path: Path, issues: List[Dict[str, str]], label: str):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append({"level": "error", "message": f"{label} is not valid JSON: {exc}"})
        return None


def _check_relative(value: str, issues: List[Dict[str, str]], label: str) -> None:
    posix = PurePosixPath(value)
    if posix.is_absolute() or ".." in posix.parts:
        issues.append({"level": "error", "message": f"{label} path must be relative and portable, got absolute or escaping path: {value}"})


def _resolve_relative(root: Path, value: str, issues: List[Dict[str, str]]) -> Path:
    posix = PurePosixPath(value)
    candidate = (root / Path(*posix.parts)).resolve()
    root_resolved = root.resolve()
    if root_resolved != candidate and root_resolved not in candidate.parents:
        issues.append({"level": "error", "message": f"path escapes package root: {value}"})
    return candidate


def _bbox_issue(mesh: trimesh.Trimesh):
    bounds = mesh.bounds
    if not all(math.isfinite(float(v)) for v in bounds.flatten()):
        return "visual mesh bbox contains non-finite values"
    extents = mesh.extents
    if any(float(v) <= 0 for v in extents):
        return "visual mesh bbox has non-positive extent"
    if any(float(v) > 1000 for v in extents):
        return "visual mesh bbox is larger than 1000 meters"
    if float(bounds[0][2]) < -0.01:
        return "visual mesh lowest z must be aligned near 0"
    return None
