import json
import zipfile
from pathlib import Path
from typing import Any, Dict


def import_ios_capture(zip_path: Path, work_dir: Path) -> Dict[str, Any]:
    extract_dir = work_dir / "ios_capture"
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(extract_dir)
    metadata_path = extract_dir / "metadata.json"
    intrinsics_path = extract_dir / "camera_intrinsics.json"
    poses_path = extract_dir / "poses" / "poses.csv"
    frames_dir = extract_dir / "frames"
    if not metadata_path.exists():
        raise ValueError("iOS capture is missing metadata.json")
    if not intrinsics_path.exists():
        raise ValueError("iOS capture is missing camera_intrinsics.json")
    if not poses_path.exists():
        raise ValueError("iOS capture is missing poses/poses.csv")
    if not frames_dir.exists() or not any(frames_dir.glob("*")):
        raise ValueError("iOS capture is missing RGB frames")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    arkit_mesh = extract_dir / "armesh" / "arkit_mesh.obj"
    return {
        "root": extract_dir,
        "metadata": metadata,
        "intrinsics_path": intrinsics_path,
        "poses_path": poses_path,
        "frames_dir": frames_dir,
        "arkit_mesh": arkit_mesh if arkit_mesh.exists() else None,
    }

