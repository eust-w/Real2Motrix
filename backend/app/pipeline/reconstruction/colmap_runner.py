import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal, Optional

from app.pipeline.utils.dependencies import DEPENDENCY_GROUPS, require_dependencies
from app.pipeline.utils.subprocess_utils import run_command

MatchStrategy = Literal["exhaustive", "sequential"]


@dataclass(frozen=True)
class SparseModelStats:
    path: Path
    cameras: int
    registered_images: int
    points: int


def reconstruct_images_with_colmap_openmvs(
    image_dir: Path,
    work_dir: Path,
    log: Optional[Callable[[str, str], None]] = None,
    *,
    single_camera: bool = False,
    match_strategy: MatchStrategy = "exhaustive",
) -> Path:
    require_dependencies(DEPENDENCY_GROUPS["colmap_openmvs"])
    if not any(image_dir.glob("*")):
        raise ValueError(f"image directory is empty: {image_dir}")

    sparse_dir = work_dir / "sparse"
    dense_dir = work_dir / "mvs"
    sparse_dir.mkdir(parents=True, exist_ok=True)
    dense_dir.mkdir(parents=True, exist_ok=True)
    database_path = work_dir / "colmap.db"

    feature_command = [
        "colmap",
        "feature_extractor",
        "--database_path",
        database_path,
        "--image_path",
        image_dir,
        "--SiftExtraction.max_num_features",
        "16384",
    ]
    if single_camera:
        feature_command.extend(
            [
                "--ImageReader.single_camera",
                "1",
                "--ImageReader.camera_model",
                "SIMPLE_RADIAL",
            ]
        )
    run_command(
        feature_command,
        cwd=work_dir,
        log=log,
    )
    if match_strategy == "sequential":
        run_command(
            [
                "colmap",
                "sequential_matcher",
                "--database_path",
                database_path,
                "--SequentialMatching.overlap",
                "15",
            ],
            cwd=work_dir,
            log=log,
        )
    else:
        run_command(["colmap", "exhaustive_matcher", "--database_path", database_path], cwd=work_dir, log=log)
    run_command(
        ["colmap", "mapper", "--database_path", database_path, "--image_path", image_dir, "--output_path", sparse_dir],
        cwd=work_dir,
        log=log,
    )
    model_dir = _select_best_sparse_model(sparse_dir, log=log)

    undistorted_dir = work_dir / "undistorted"
    run_command(
        [
            "colmap",
            "image_undistorter",
            "--image_path",
            image_dir,
            "--input_path",
            model_dir,
            "--output_path",
            undistorted_dir,
            "--output_type",
            "COLMAP",
            "--max_image_size",
            "1600",
        ],
        cwd=work_dir,
        log=log,
    )
    if not (undistorted_dir / "sparse" / "cameras.bin").exists():
        raise RuntimeError("COLMAP image_undistorter completed but did not produce sparse/cameras.bin")

    scene_mvs = dense_dir / "scene.mvs"
    run_command(
        [
            "InterfaceCOLMAP",
            "-i",
            undistorted_dir,
            "-o",
            scene_mvs,
            "--image-folder",
            undistorted_dir / "images",
        ],
        cwd=work_dir,
        log=log,
    )
    run_command(
        [
            "DensifyPointCloud",
            "-i",
            scene_mvs,
            "--resolution-level",
            "0",
            "--max-resolution",
            "1600",
            "--number-views",
            "8",
        ],
        cwd=dense_dir,
        log=log,
    )
    dense_mvs = dense_dir / "scene_dense.mvs"
    if not dense_mvs.exists():
        raise RuntimeError("DensifyPointCloud completed but scene_dense.mvs was not found")

    mesh_ply = dense_dir / "scene_dense_mesh.ply"
    _unlink_if_exists(mesh_ply)
    run_command(["ReconstructMesh", "-i", dense_mvs, "-o", mesh_ply], cwd=dense_dir, log=log)
    if not mesh_ply.exists():
        weak_mesh_ply = dense_dir / "scene_dense_mesh_weak.ply"
        _unlink_if_exists(weak_mesh_ply)
        if log:
            log(
                "warn",
                "OpenMVS default mesh cleanup produced no mesh; retrying with weak mesh cleanup. "
                "The result may be low-detail if the capture has little parallax or texture.",
            )
        run_command(
            [
                "ReconstructMesh",
                "-i",
                dense_mvs,
                "-o",
                weak_mesh_ply,
                "--remove-spurious",
                "0",
                "--remove-spikes",
                "0",
                "--close-holes",
                "0",
                "--smooth",
                "0",
            ],
            cwd=dense_dir,
            log=log,
        )
        if weak_mesh_ply.exists() and _read_ply_face_count(weak_mesh_ply) > 0:
            if log:
                log(
                    "warn",
                    "Using weak mesh fallback because the default OpenMVS cleanup removed all faces. "
                    "Recapture with slower motion, more side-to-side parallax, and more textured overlap for better quality.",
                )
            return weak_mesh_ply
        raise RuntimeError(
            "ReconstructMesh produced no usable mesh. The capture appears under-constrained; "
            "recapture with slower motion, more side-to-side parallax, and more textured overlap."
        )

    refined_ply = dense_dir / "scene_dense_mesh_refine.ply"
    _unlink_if_exists(refined_ply)
    run_command(["RefineMesh", "-i", dense_mvs, "-m", mesh_ply, "-o", refined_ply], cwd=dense_dir, log=log)
    if not refined_ply.exists():
        raise RuntimeError("RefineMesh completed but scene_dense_mesh_refine.ply was not found")

    textured_obj = dense_dir / "scene_dense_mesh_refine_texture.obj"
    _unlink_if_exists(textured_obj)
    run_command(
        [
            "TextureMesh",
            "-i",
            dense_mvs,
            "-m",
            refined_ply,
            "--export-type",
            "obj",
            "-o",
            textured_obj,
        ],
        cwd=dense_dir,
        log=log,
    )
    if not textured_obj.exists():
        raise RuntimeError("OpenMVS completed but textured OBJ was not found")
    return textured_obj


def _unlink_if_exists(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _read_ply_face_count(path: Path) -> int:
    header = bytearray()
    with path.open("rb") as handle:
        while b"end_header\n" not in header:
            chunk = handle.readline()
            if not chunk:
                break
            header.extend(chunk)
            if len(header) > 65536:
                break
    text = header.decode("ascii", errors="ignore")
    match = re.search(r"^element\s+face\s+(\d+)\s*$", text, re.MULTILINE)
    if not match:
        return 0
    return int(match.group(1))


def _select_best_sparse_model(
    sparse_dir: Path,
    log: Optional[Callable[[str, str], None]] = None,
) -> Path:
    candidates = sorted(path for path in sparse_dir.iterdir() if path.is_dir())
    if not candidates:
        raise RuntimeError("COLMAP mapper completed but did not produce any sparse model")

    stats = [_read_sparse_model_stats(candidate) for candidate in candidates]
    best = max(stats, key=lambda item: (item.registered_images, item.points, -int(item.path.name) if item.path.name.isdigit() else 0))
    if best.registered_images < 2 or best.points < 1:
        raise RuntimeError("COLMAP mapper produced only degenerate sparse models")
    if log:
        rel = best.path.relative_to(sparse_dir.parent)
        log(
            "info",
            f"selected COLMAP model {rel} with {best.registered_images} registered images, "
            f"{best.cameras} cameras, {best.points} sparse points",
        )
    return best.path


def _read_sparse_model_stats(model_dir: Path) -> SparseModelStats:
    process = subprocess.run(
        ["colmap", "model_analyzer", "--path", str(model_dir)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(f"COLMAP model_analyzer failed for {model_dir}: {process.stdout}")
    return SparseModelStats(
        path=model_dir,
        cameras=_extract_model_analyzer_int(process.stdout, "Cameras"),
        registered_images=_extract_model_analyzer_int(process.stdout, "Registered images"),
        points=_extract_model_analyzer_int(process.stdout, "Points"),
    )


def _extract_model_analyzer_int(output: str, label: str) -> int:
    match = re.search(rf"{re.escape(label)}:\s+(\d+)", output)
    if not match:
        raise RuntimeError(f"COLMAP model_analyzer output did not include {label!r}")
    return int(match.group(1))
