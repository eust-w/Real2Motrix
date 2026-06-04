import json
import math
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Tuple

from app.database import Database, json_dumps, json_loads, utc_now
from app.services.capture_session_service import create_capture_session
from app.services.job_service import create_job
from app.services.project_service import update_project_status


CELL_SIZE_M = 0.5


def create_live_session(
    db: Database,
    project: Dict[str, Any],
    capture_type: str,
    capture_mode: str,
    target_type: str,
    device_model: str,
    has_lidar: bool,
) -> Dict[str, Any]:
    session_id = str(uuid.uuid4())
    root_dir = Path(project["root_dir"]) / "live_sessions" / session_id
    for folder in ("frames", "depth", "mesh", "poses", "quality"):
        (root_dir / folder).mkdir(parents=True, exist_ok=True)
    preview_path = root_dir / "preview.obj"
    _write_preview_obj(preview_path, [])
    now = utc_now()
    db.execute(
        """
        INSERT INTO live_scan_sessions (
            id, project_id, status, capture_type, capture_mode, target_type, device_model,
            has_lidar, root_dir, frame_count, depth_frame_count, mesh_chunk_count,
            coverage_json, quality_json, last_pose_json, preview_path, archive_path,
            created_at, updated_at, finished_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            project["id"],
            "running",
            capture_type,
            capture_mode,
            target_type,
            device_model,
            1 if has_lidar else 0,
            str(root_dir),
            0,
            0,
            0,
            json_dumps(empty_coverage()),
            json_dumps(empty_quality()),
            json_dumps({}),
            str(preview_path),
            None,
            now,
            now,
            None,
        ),
    )
    update_project_status(db, project["id"], "running")
    return get_live_session(db, session_id)


def list_live_sessions(db: Database, project_id: str) -> List[Dict[str, Any]]:
    rows = db.fetch_all(
        "SELECT * FROM live_scan_sessions WHERE project_id = ? ORDER BY updated_at DESC, created_at DESC",
        (project_id,),
    )
    return [normalize_live_session(row) for row in rows]


def get_live_session(db: Database, session_id: str) -> Dict[str, Any]:
    row = db.fetch_one("SELECT * FROM live_scan_sessions WHERE id = ?", (session_id,))
    if not row:
        raise KeyError(session_id)
    return normalize_live_session(row)


def add_live_frame(
    db: Database,
    session_id: str,
    frame_index: int,
    timestamp: float,
    pose: Dict[str, Any],
    quality: Dict[str, Any],
    intrinsics: Dict[str, Any],
    frame_file: BinaryIO,
    frame_filename: str,
    depth_file: Optional[BinaryIO] = None,
    depth_filename: Optional[str] = None,
) -> Dict[str, Any]:
    session = get_live_session(db, session_id)
    if session["status"] != "running":
        raise ValueError("live scan session is not running")
    root = Path(session["root_dir"])
    frame_path = root / "frames" / frame_name(frame_index, frame_filename or "frame.jpg")
    frame_path.parent.mkdir(parents=True, exist_ok=True)
    with frame_path.open("wb") as target:
        shutil.copyfileobj(frame_file, target)

    depth_path: Optional[Path] = None
    if depth_file is not None:
        depth_path = root / "depth" / depth_name(frame_index, depth_filename or "depth.png")
        depth_path.parent.mkdir(parents=True, exist_ok=True)
        with depth_path.open("wb") as target:
            shutil.copyfileobj(depth_file, target)

    db.execute(
        "DELETE FROM live_scan_frames WHERE session_id = ? AND frame_index = ?",
        (session_id, frame_index),
    )
    db.execute(
        """
        INSERT INTO live_scan_frames (
            session_id, frame_index, timestamp, frame_path, depth_path,
            pose_json, quality_json, intrinsics_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            frame_index,
            timestamp,
            str(frame_path),
            str(depth_path) if depth_path else None,
            json_dumps(pose),
            json_dumps(quality),
            json_dumps(intrinsics),
            utc_now(),
        ),
    )
    refreshed = refresh_live_session_metrics(db, session_id)
    _append_pose_csv(root, frame_index, timestamp, pose)
    return refreshed


def add_live_mesh_chunk(
    db: Database,
    session_id: str,
    chunk_index: int,
    mesh_file: BinaryIO,
    mesh_filename: str,
) -> Dict[str, Any]:
    session = get_live_session(db, session_id)
    if session["status"] != "running":
        raise ValueError("live scan session is not running")
    root = Path(session["root_dir"])
    mesh_path = root / "mesh" / mesh_name(chunk_index, mesh_filename or "mesh.obj")
    mesh_path.parent.mkdir(parents=True, exist_ok=True)
    with mesh_path.open("wb") as target:
        shutil.copyfileobj(mesh_file, target)
    mesh_count = len(list((root / "mesh").glob("*.obj")))
    db.execute(
        "UPDATE live_scan_sessions SET mesh_chunk_count = ?, updated_at = ? WHERE id = ?",
        (mesh_count, utc_now(), session_id),
    )
    return refresh_live_session_metrics(db, session_id)


def refresh_live_session_metrics(db: Database, session_id: str) -> Dict[str, Any]:
    frames = live_frames(db, session_id)
    positions = [position for position in (_extract_position(frame["pose_json"]) for frame in frames) if position]
    coverage = coverage_from_positions(positions)
    quality = aggregate_quality(frames, coverage)
    preview_path = Path(get_live_session(db, session_id)["preview_path"] or Path(frames[0]["frame_path"]).parents[1] / "preview.obj")
    _write_preview_obj(preview_path, positions, coverage, mesh_dir=preview_path.parent / "mesh")
    last_pose = json_loads(frames[-1]["pose_json"]) if frames else {}
    db.execute(
        """
        UPDATE live_scan_sessions
        SET frame_count = ?, depth_frame_count = ?, coverage_json = ?, quality_json = ?,
            last_pose_json = ?, preview_path = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            len(frames),
            sum(1 for frame in frames if frame["depth_path"]),
            json_dumps(coverage),
            json_dumps(quality),
            json_dumps(last_pose),
            str(preview_path),
            utc_now(),
            session_id,
        ),
    )
    return get_live_session(db, session_id)


def finish_live_session(db: Database, project: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    session = get_live_session(db, session_id)
    if session["project_id"] != project["id"]:
        raise ValueError("live scan session belongs to another project")
    if session["frame_count"] == 0:
        raise ValueError("live scan session has no frames")
    archive_path = build_live_capture_archive(db, session_id)
    capture_session = create_capture_session(
        db,
        project_id=project["id"],
        zip_path=archive_path,
        capture_type=session["capture_type"],
        capture_mode=session["capture_mode"],
        device_model=session["device_model"],
        has_lidar=session["has_lidar"],
    )
    job = create_job(
        db,
        project_id=project["id"],
        source_type="ios_capture",
        input_path=archive_path,
        capture_session_id=capture_session["id"],
        params={"fast_mode": False, "live_session_id": session_id},
    )
    now = utc_now()
    db.execute(
        """
        UPDATE live_scan_sessions
        SET status = 'completed', archive_path = ?, finished_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (str(archive_path), now, now, session_id),
    )
    update_project_status(db, project["id"], "queued")
    return {"live_session": get_live_session(db, session_id), "capture_session": capture_session, "job": job}


def build_live_capture_archive(db: Database, session_id: str) -> Path:
    session = get_live_session(db, session_id)
    frames = live_frames(db, session_id)
    if not frames:
        raise ValueError("live scan session has no frames")
    root = Path(session["root_dir"])
    rebuild_pose_csv(root, frames)
    intrinsics = latest_intrinsics(frames)
    (root / "camera_intrinsics.json").write_text(json.dumps(intrinsics, indent=2, ensure_ascii=False), encoding="utf-8")
    metadata = capture_metadata(session, frames, intrinsics)
    (root / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    quality_report = dict(session["quality_json"])
    quality_report["coverage"] = session["coverage_json"]
    (root / "quality").mkdir(parents=True, exist_ok=True)
    (root / "quality" / "quality_report.json").write_text(
        json.dumps(quality_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    latest_mesh = latest_mesh_snapshot(root)
    if latest_mesh:
        (root / "armesh").mkdir(parents=True, exist_ok=True)
        shutil.copy2(latest_mesh, root / "armesh" / "arkit_mesh.obj")
    archive_path = root / "live_capture.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path == archive_path or not path.is_file():
                continue
            archive.write(path, path.relative_to(root))
    return archive_path


def live_frames(db: Database, session_id: str) -> List[Dict[str, Any]]:
    rows = db.fetch_all(
        "SELECT * FROM live_scan_frames WHERE session_id = ? ORDER BY frame_index ASC",
        (session_id,),
    )
    return rows


def normalize_live_session(row: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(row)
    result["has_lidar"] = bool(result["has_lidar"])
    result["coverage_json"] = json_loads(result["coverage_json"])
    result["quality_json"] = json_loads(result["quality_json"])
    result["last_pose_json"] = json_loads(result["last_pose_json"])
    return result


def empty_coverage() -> Dict[str, Any]:
    return {
        "coverage_score": 0,
        "covered_cell_count": 0,
        "target_cell_count": 0,
        "cell_size_m": CELL_SIZE_M,
        "bounds": None,
        "cells": [],
        "weak_cells": [],
        "camera_path": [],
        "last_position": None,
    }


def empty_quality() -> Dict[str, Any]:
    return {
        "frame_count": 0,
        "average_brightness": 0,
        "average_blur_score": 0,
        "tracking_lost_count": 0,
        "warnings": ["需要开始手机扫描"],
    }


def parse_json_object(value: str, field_name: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(value) if value else {}
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return parsed


def frame_name(frame_index: int, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".heic"}:
        suffix = ".jpg"
    return f"frame_{frame_index:06d}{suffix}"


def depth_name(frame_index: int, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".png", ".tiff", ".tif", ".exr"}:
        suffix = ".png"
    return f"depth_{frame_index:06d}{suffix}"


def mesh_name(chunk_index: int, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix != ".obj":
        suffix = ".obj"
    if chunk_index <= 0:
        return f"mesh_snapshot{suffix}"
    return f"mesh_{chunk_index:06d}{suffix}"


def coverage_from_positions(positions: List[Tuple[float, float, float]]) -> Dict[str, Any]:
    if not positions:
        return empty_coverage()
    counts: Dict[Tuple[int, int], int] = {}
    for x, _, z in positions:
        key = (math.floor(x / CELL_SIZE_M), math.floor(z / CELL_SIZE_M))
        counts[key] = counts.get(key, 0) + 1
    xs = [cell[0] for cell in counts]
    zs = [cell[1] for cell in counts]
    min_x, max_x = min(xs) - 1, max(xs) + 1
    min_z, max_z = min(zs) - 1, max(zs) + 1
    total_cells = (max_x - min_x + 1) * (max_z - min_z + 1)
    weak_cells = [
        {"ix": ix, "iz": iz, "x": round((ix + 0.5) * CELL_SIZE_M, 3), "z": round((iz + 0.5) * CELL_SIZE_M, 3), "count": counts.get((ix, iz), 0)}
        for ix in range(min_x, max_x + 1)
        for iz in range(min_z, max_z + 1)
        if counts.get((ix, iz), 0) == 0
    ][:32]
    cells = [
        {"ix": ix, "iz": iz, "x": round((ix + 0.5) * CELL_SIZE_M, 3), "z": round((iz + 0.5) * CELL_SIZE_M, 3), "count": count}
        for (ix, iz), count in sorted(counts.items())
    ]
    return {
        "coverage_score": round(len(counts) / total_cells, 4) if total_cells else 0,
        "covered_cell_count": len(counts),
        "target_cell_count": total_cells,
        "cell_size_m": CELL_SIZE_M,
        "bounds": {
            "min_x": round(min_x * CELL_SIZE_M, 3),
            "max_x": round((max_x + 1) * CELL_SIZE_M, 3),
            "min_z": round(min_z * CELL_SIZE_M, 3),
            "max_z": round((max_z + 1) * CELL_SIZE_M, 3),
        },
        "cells": cells,
        "weak_cells": weak_cells,
        "camera_path": [
            {"x": round(x, 4), "y": round(y, 4), "z": round(z, 4)}
            for x, y, z in positions[-240:]
        ],
        "last_position": {"x": round(positions[-1][0], 4), "y": round(positions[-1][1], 4), "z": round(positions[-1][2], 4)},
    }


def aggregate_quality(frames: List[Dict[str, Any]], coverage: Dict[str, Any]) -> Dict[str, Any]:
    qualities = [json_loads(frame["quality_json"]) for frame in frames]
    brightness_values = [float(value) for value in (_number(q.get("brightness")) for q in qualities) if value is not None]
    blur_values = [
        float(value)
        for value in (_number(q.get("blur_score", q.get("blur"))) for q in qualities)
        if value is not None
    ]
    tracking_lost = sum(1 for q in qualities if str(q.get("tracking_state", "")).lower() in {"not_available", "limited"})
    average_brightness = round(sum(brightness_values) / len(brightness_values), 4) if brightness_values else 0
    average_blur = round(sum(blur_values) / len(blur_values), 4) if blur_values else 0
    warnings: List[str] = []
    if len(frames) < 20:
        warnings.append("帧数偏少，建议继续扫描")
    if coverage.get("coverage_score", 0) < 0.45:
        warnings.append("覆盖率偏低，请补扫弱覆盖区域")
    if brightness_values and average_brightness < 0.25:
        warnings.append("画面偏暗，建议补光或放慢扫描")
    if blur_values and average_blur < 10:
        warnings.append("画面可能模糊，建议移动更慢并保持稳定")
    if tracking_lost:
        warnings.append("存在 AR 跟踪不稳定帧，请回到纹理丰富区域继续扫描")
    return {
        "frame_count": len(frames),
        "average_brightness": average_brightness,
        "average_blur_score": average_blur,
        "tracking_lost_count": tracking_lost,
        "warnings": warnings,
    }


def latest_intrinsics(frames: List[Dict[str, Any]]) -> Dict[str, Any]:
    for frame in reversed(frames):
        intrinsics = json_loads(frame["intrinsics_json"])
        if intrinsics:
            return {
                "camera_model": intrinsics.get("camera_model", "pinhole"),
                "width": int(intrinsics.get("width") or 0),
                "height": int(intrinsics.get("height") or 0),
                "fx": float(intrinsics.get("fx") or 0),
                "fy": float(intrinsics.get("fy") or 0),
                "cx": float(intrinsics.get("cx") or 0),
                "cy": float(intrinsics.get("cy") or 0),
                "distortion": intrinsics.get("distortion", []),
                "unit": intrinsics.get("unit", "pixel"),
            }
    return {"camera_model": "pinhole", "width": 0, "height": 0, "fx": 0, "fy": 0, "cx": 0, "cy": 0, "distortion": [], "unit": "pixel"}


def capture_metadata(session: Dict[str, Any], frames: List[Dict[str, Any]], intrinsics: Dict[str, Any]) -> Dict[str, Any]:
    first_timestamp = float(frames[0]["timestamp"])
    last_timestamp = float(frames[-1]["timestamp"])
    return {
        "app": "Real2Motrix Live Scan",
        "capture_id": session["id"],
        "project_id": session["project_id"],
        "live_session_id": session["id"],
        "capture_type": session["capture_type"],
        "capture_mode": session["capture_mode"],
        "target_type": session["target_type"],
        "device_model": session["device_model"],
        "has_lidar": session["has_lidar"],
        "has_depth": session["depth_frame_count"] > 0,
        "has_arkit_pose": True,
        "unit": "meter",
        "coordinate_system": "arkit_world",
        "frame_count": session["frame_count"],
        "depth_frame_count": session["depth_frame_count"],
        "resolution": [intrinsics.get("width", 0), intrinsics.get("height", 0)],
        "created_at": session["created_at"],
        "duration_seconds": max(0, round(last_timestamp - first_timestamp, 4)),
    }


def rebuild_pose_csv(root: Path, frames: List[Dict[str, Any]]) -> None:
    poses_path = root / "poses" / "poses.csv"
    poses_path.parent.mkdir(parents=True, exist_ok=True)
    poses_path.write_text("timestamp,frame_id,tx,ty,tz,qx,qy,qz,qw,tracking_state\n", encoding="utf-8")
    for frame in frames:
        pose = json_loads(frame["pose_json"])
        _append_pose_csv(root, int(frame["frame_index"]), float(frame["timestamp"]), pose)


def _append_pose_csv(root: Path, frame_index: int, timestamp: float, pose: Dict[str, Any]) -> None:
    poses_path = root / "poses" / "poses.csv"
    if not poses_path.exists():
        poses_path.parent.mkdir(parents=True, exist_ok=True)
        poses_path.write_text("timestamp,frame_id,tx,ty,tz,qx,qy,qz,qw,tracking_state\n", encoding="utf-8")
    position = _extract_position(pose) or (0.0, 0.0, 0.0)
    quaternion = _extract_quaternion(pose)
    tracking_state = str(pose.get("tracking_state", pose.get("trackingState", "normal")))
    with poses_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"{timestamp},{frame_index},{position[0]},{position[1]},{position[2]},"
            f"{quaternion[0]},{quaternion[1]},{quaternion[2]},{quaternion[3]},{tracking_state}\n"
        )


def latest_mesh_snapshot(root: Path) -> Optional[Path]:
    mesh_dir = root / "mesh"
    if not mesh_dir.exists():
        return None
    snapshots = sorted(mesh_dir.glob("mesh_snapshot.obj"), key=lambda item: item.stat().st_mtime, reverse=True)
    if snapshots:
        return snapshots[0]
    chunks = sorted(mesh_dir.glob("*.obj"), key=lambda item: item.stat().st_mtime, reverse=True)
    return chunks[0] if chunks else None


def _write_preview_obj(
    path: Path,
    positions: List[Tuple[float, float, float]],
    coverage: Optional[Dict[str, Any]] = None,
    mesh_dir: Optional[Path] = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Real2Motrix live scan preview"]
    for x, y, z in positions:
        lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    if len(positions) >= 2:
        lines.append("l " + " ".join(str(index) for index in range(1, len(positions) + 1)))
    coverage = coverage or empty_coverage()
    start_index = len(positions) + 1
    for cell in coverage.get("cells", [])[:128]:
        ix = int(cell["ix"])
        iz = int(cell["iz"])
        x0 = ix * CELL_SIZE_M
        x1 = x0 + CELL_SIZE_M
        z0 = iz * CELL_SIZE_M
        z1 = z0 + CELL_SIZE_M
        lines.extend(
            [
                f"v {x0:.6f} 0.000000 {z0:.6f}",
                f"v {x1:.6f} 0.000000 {z0:.6f}",
                f"v {x1:.6f} 0.000000 {z1:.6f}",
                f"v {x0:.6f} 0.000000 {z1:.6f}",
                f"l {start_index} {start_index + 1} {start_index + 2} {start_index + 3} {start_index}",
            ]
        )
        start_index += 4
    if mesh_dir and mesh_dir.exists():
        vertex_offset = start_index - 1
        for mesh_path in sorted(mesh_dir.glob("*.obj")):
            vertex_offset = _append_obj_file(lines, mesh_path, vertex_offset)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _append_obj_file(lines: List[str], mesh_path: Path, vertex_offset: int) -> int:
    local_vertices = 0
    for raw_line in mesh_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("v "):
            local_vertices += 1
            lines.append(stripped)
            continue
        if stripped.startswith(("f ", "l ")):
            parts = stripped.split()
            remapped = [parts[0]]
            for token in parts[1:]:
                pieces = token.split("/")
                try:
                    index = int(pieces[0])
                except ValueError:
                    remapped.append(token)
                    continue
                if index > 0:
                    pieces[0] = str(index + vertex_offset)
                remapped.append("/".join(pieces))
            lines.append(" ".join(remapped))
    return vertex_offset + local_vertices


def _extract_position(pose: Any) -> Optional[Tuple[float, float, float]]:
    pose = json_loads(pose) if isinstance(pose, str) else pose
    if not isinstance(pose, dict):
        return None
    position = pose.get("position") or pose.get("translation")
    if isinstance(position, list) and len(position) >= 3:
        return (float(position[0]), float(position[1]), float(position[2]))
    transform = pose.get("transform") or pose.get("camera_transform") or pose.get("cameraTransform")
    if isinstance(transform, list) and len(transform) >= 16:
        return (float(transform[12]), float(transform[13]), float(transform[14]))
    camera = pose.get("camera")
    if isinstance(camera, dict):
        return _extract_position(camera)
    return None


def _extract_quaternion(pose: Dict[str, Any]) -> Tuple[float, float, float, float]:
    quaternion = pose.get("quaternion") or pose.get("rotation")
    if isinstance(quaternion, list) and len(quaternion) >= 4:
        return (float(quaternion[0]), float(quaternion[1]), float(quaternion[2]), float(quaternion[3]))
    return (0.0, 0.0, 0.0, 1.0)


def _number(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    return None
