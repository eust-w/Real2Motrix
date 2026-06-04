import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional

from app.pipeline.capture.ios_capture_import import import_ios_capture
from app.pipeline.capture.video_extract import extract_video_frames
from app.pipeline.mesh.cleanup import clean_visual_mesh
from app.pipeline.mesh.convert import MESH_EXTENSIONS, convert_mesh_to_obj
from app.pipeline.mesh.io import export_obj, load_mesh
from app.pipeline.mesh.scene_split import split_scene_objects
from app.pipeline.motrix.package import prepare_package_dir, zip_package
from app.pipeline.motrix.validate import validate_package
from app.pipeline.motrix.writers import write_scene_files
from app.pipeline.pointcloud.open3d_runner import pointcloud_to_mesh
from app.pipeline.reconstruction.colmap_runner import reconstruct_images_with_colmap_openmvs


LogFn = Optional[Callable[[str, str], None]]


@dataclass
class PipelineResult:
    package_dir: Path
    package_zip: Path
    validation_report: Dict[str, Any]


def run_full_pipeline(
    source_type: str,
    input_path: Path,
    project_id: str,
    output_root: Path,
    log: LogFn = None,
    fast_mode: bool = False,
) -> PipelineResult:
    work_dir = output_root / project_id / "work"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    source_type = source_type.lower()
    source_info = {"source_type": source_type, "input_path": str(input_path.name)}

    if source_type == "mesh":
        return run_mesh_pipeline(input_path, project_id, output_root, source_info, log=log, work_dir=work_dir)
    if source_type == "video":
        frames = extract_video_frames(input_path, work_dir / "frames", log=log)
        mesh = reconstruct_images_with_colmap_openmvs(
            frames,
            work_dir / "reconstruction",
            log=log,
            single_camera=True,
            match_strategy="sequential",
        )
        return run_mesh_pipeline(mesh, project_id, output_root, source_info, log=log, work_dir=work_dir)
    if source_type == "images":
        image_dir = input_path if input_path.is_dir() else _copy_images_to_dir([input_path], work_dir / "frames")
        mesh = reconstruct_images_with_colmap_openmvs(image_dir, work_dir / "reconstruction", log=log)
        return run_mesh_pipeline(mesh, project_id, output_root, source_info, log=log, work_dir=work_dir)
    if source_type == "ios_capture":
        capture = import_ios_capture(input_path, work_dir)
        source_info.update(capture["metadata"])
        if fast_mode and capture["arkit_mesh"]:
            return run_mesh_pipeline(capture["arkit_mesh"], project_id, output_root, source_info, log=log, work_dir=work_dir)
        mesh = reconstruct_images_with_colmap_openmvs(
            capture["frames_dir"],
            work_dir / "reconstruction",
            log=log,
            single_camera=True,
            match_strategy="sequential",
        )
        return run_mesh_pipeline(mesh, project_id, output_root, source_info, log=log, work_dir=work_dir)
    if source_type in {"polycam", "scaniverse", "nerfstudio"}:
        mesh = _find_mesh_input(input_path, work_dir)
        return run_mesh_pipeline(mesh, project_id, output_root, source_info, log=log, work_dir=work_dir)
    if source_type == "pointcloud":
        mesh = pointcloud_to_mesh(input_path, work_dir / "pointcloud_mesh.obj")
        return run_mesh_pipeline(mesh, project_id, output_root, source_info, log=log, work_dir=work_dir)
    raise ValueError(f"unsupported source_type: {source_type}")


def run_mesh_pipeline(
    source_mesh: Path,
    project_id: str,
    output_root: Path,
    source_info: Dict[str, Any],
    log: LogFn = None,
    work_dir: Optional[Path] = None,
) -> PipelineResult:
    if log:
        log("info", f"loading mesh {source_mesh}")
    output_root = Path(output_root)
    work_dir = work_dir or (output_root / project_id / "work")
    work_dir.mkdir(parents=True, exist_ok=True)
    package_dir = prepare_package_dir(output_root, project_id)
    converted = convert_mesh_to_obj(source_mesh, work_dir, log=log)
    visual = clean_visual_mesh(load_mesh(converted), prune_small_components=False)
    scene_assets = split_scene_objects(visual)
    if log:
        log("info", f"segmented mesh into {len(scene_assets.objects)} object asset candidates")
    visual_path = package_dir / "meshes" / "scene_visual.obj"
    collision_path = package_dir / "meshes" / "scene_collision.obj"
    export_obj(scene_assets.scene_visual, visual_path)
    export_obj(scene_assets.scene_collision, collision_path)
    for object_asset in scene_assets.objects:
        export_obj(object_asset.visual, package_dir / object_asset.manifest["visual_mesh"])
        export_obj(object_asset.collision, package_dir / object_asset.manifest["collision_mesh"])

    scene_manifest = {
        "id": "static_scene",
        "role": "environment",
        "visual_mesh": "meshes/scene_visual.obj",
        "collision_mesh": "meshes/scene_collision.obj",
        "visual_faces": int(len(scene_assets.scene_visual.faces)),
        "collision_faces": int(len(scene_assets.scene_collision.faces)),
        "bbox": scene_assets.scene_visual.bounds.tolist(),
        "binding": {"type": "static_world", "body": "static_scene"},
        "gaussian_splat": None,
    }
    object_manifests = [object_asset.manifest for object_asset in scene_assets.objects]
    manifest = {
        "schema_version": 2,
        "project_id": project_id,
        "unit": "meter",
        "coordinate_system": "motrix_world",
        "scene": scene_manifest,
        "objects": object_manifests,
        "segmentation": scene_assets.segmentation,
        "source_visual_faces": int(len(visual.faces)),
        "source_bbox": visual.bounds.tolist(),
        "visual_mesh": "meshes/scene_visual.obj",
        "collision_mesh": "meshes/scene_collision.obj",
        "visual_faces": scene_manifest["visual_faces"],
        "collision_faces": scene_manifest["collision_faces"],
        "bbox": scene_manifest["bbox"],
    }
    write_scene_files(package_dir, manifest=manifest, source_info=source_info)
    reconstruction_report = {
        "source": source_info,
        "mesh_pipeline": {
            "source_visual_faces": int(len(visual.faces)),
            "scene_visual_faces": scene_manifest["visual_faces"],
            "scene_collision_faces": scene_manifest["collision_faces"],
            "object_count": len(object_manifests),
            "segmentation": scene_assets.segmentation,
            "collision_strategy": "convex_hull_or_bounding_box",
        },
    }
    (package_dir / "metadata" / "reconstruction_report.json").write_text(
        json.dumps(reconstruction_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    validation_report = validate_package(package_dir)
    if not validation_report["valid"]:
        raise RuntimeError("Motrix package validation failed: " + json.dumps(validation_report["issues"], ensure_ascii=False))
    package_zip = zip_package(package_dir)
    return PipelineResult(package_dir=package_dir, package_zip=package_zip, validation_report=validation_report)


def _copy_images_to_dir(images: Iterable[Path], target: Path) -> Path:
    target.mkdir(parents=True, exist_ok=True)
    for image in images:
        shutil.copy2(image, target / image.name)
    return target


def _find_mesh_input(input_path: Path, work_dir: Path) -> Path:
    input_path = Path(input_path)
    search_root = input_path
    if input_path.suffix.lower() == ".zip":
        import zipfile

        search_root = work_dir / "archive_input"
        search_root.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(input_path) as archive:
            archive.extractall(search_root)
    if search_root.is_file():
        return search_root
    candidates = [
        path
        for path in search_root.rglob("*")
        if path.is_file() and (path.suffix.lower() in MESH_EXTENSIONS or path.suffix.lower() == ".fbx")
    ]
    if not candidates:
        raise ValueError(f"no supported mesh found in {input_path}")
    candidates.sort(key=lambda path: path.stat().st_size, reverse=True)
    return candidates[0]
