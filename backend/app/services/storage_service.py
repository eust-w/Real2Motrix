import shutil
from pathlib import Path
from typing import Iterable

from fastapi import UploadFile


def ensure_relative_child(root: Path, relative_path: str) -> Path:
    root = root.resolve()
    candidate = (root / relative_path).resolve()
    if root != candidate and root not in candidate.parents:
        raise ValueError(f"path escapes root: {relative_path}")
    return root / relative_path


def safe_filename(filename: str) -> str:
    cleaned = Path(filename).name.strip()
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError("invalid filename")
    return cleaned.replace("/", "_").replace("\\", "_")


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def copy_upload_file(upload: UploadFile, destination: Path) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with destination.open("wb") as out:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            out.write(chunk)
    upload.file.seek(0)
    return total


def common_parent(paths: Iterable[Path]) -> Path:
    resolved = [path.resolve() for path in paths]
    if not resolved:
        raise ValueError("no paths supplied")
    parent = resolved[0].parent
    for path in resolved[1:]:
        if path.parent != parent:
            raise ValueError("all input files must be in the same project upload directory")
    return parent
