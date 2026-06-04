import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


class DependencyError(RuntimeError):
    pass


@dataclass(frozen=True)
class Dependency:
    name: str
    executable: Optional[str]
    available: bool
    version: Optional[str] = None


DEPENDENCY_GROUPS = {
    "base": ["ffmpeg", "python3", "node"],
    "colmap_openmvs": [
        "colmap",
        "InterfaceCOLMAP",
        "DensifyPointCloud",
        "ReconstructMesh",
        "RefineMesh",
        "TextureMesh",
    ],
    "blender": ["blender"],
    "ios_build": ["swift", "xcodebuild"],
}


def inspect_dependency(name: str) -> Dependency:
    executable = shutil.which(name)
    version = None
    if executable:
        try:
            result = subprocess.run(
                [executable, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            version = (result.stdout or result.stderr).splitlines()[0] if (result.stdout or result.stderr) else None
        except Exception:
            version = None
    return Dependency(name=name, executable=executable, available=bool(executable), version=version)


def inspect_dependencies(names: Optional[Iterable[str]] = None) -> Dict[str, Dict]:
    selected = list(names) if names else sorted({item for group in DEPENDENCY_GROUPS.values() for item in group})
    return {name: inspect_dependency(name).__dict__ for name in selected}


def require_dependencies(names: Iterable[str]) -> None:
    missing: List[str] = [name for name in names if not shutil.which(name)]
    if missing:
        raise DependencyError(
            "Missing required local tools: "
            + ", ".join(missing)
            + ". Install them locally and ensure they are on PATH; Real2Motrix does not fake or auto-install pipeline tools."
        )

