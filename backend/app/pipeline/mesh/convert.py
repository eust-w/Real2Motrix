from pathlib import Path
from typing import Callable, Optional

import trimesh

from app.pipeline.utils.dependencies import require_dependencies
from app.pipeline.utils.subprocess_utils import run_command


MESH_EXTENSIONS = {".obj", ".glb", ".gltf", ".stl", ".ply"}


def convert_mesh_to_obj(
    source_path: Path,
    work_dir: Path,
    log: Optional[Callable[[str, str], None]] = None,
) -> Path:
    source_path = Path(source_path)
    suffix = source_path.suffix.lower()
    output = work_dir / "converted" / "source.obj"
    output.parent.mkdir(parents=True, exist_ok=True)
    if suffix == ".obj":
        return source_path
    if suffix in {".glb", ".gltf", ".stl", ".ply"}:
        mesh = trimesh.load(source_path, force="scene")
        mesh.export(output)
        return output
    if suffix == ".fbx":
        require_dependencies(["blender"])
        script = work_dir / "converted" / "fbx_to_obj.py"
        script.write_text(
            """
import bpy
import sys
bpy.ops.object.delete()
bpy.ops.import_scene.fbx(filepath=sys.argv[-2])
bpy.ops.export_scene.obj(filepath=sys.argv[-1])
""".strip(),
            encoding="utf-8",
        )
        run_command(["blender", "--background", "--python", script, "--", source_path, output], cwd=work_dir, log=log)
        return output
    raise ValueError(f"unsupported mesh format: {source_path.suffix}")
