import shutil
import zipfile
from pathlib import Path


def zip_package(package_dir: Path) -> Path:
    zip_path = package_dir.parent / "motrix_scene.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(package_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(package_dir.parent))
    return zip_path


def prepare_package_dir(output_root: Path, project_id: str) -> Path:
    project_output = output_root / project_id
    package_dir = project_output / "motrix_scene"
    if package_dir.exists():
        shutil.rmtree(package_dir)
    (package_dir / "meshes").mkdir(parents=True, exist_ok=True)
    (package_dir / "textures").mkdir(parents=True, exist_ok=True)
    (package_dir / "metadata").mkdir(parents=True, exist_ok=True)
    (package_dir / "raw").mkdir(parents=True, exist_ok=True)
    return package_dir

