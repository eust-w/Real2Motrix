"""Generate an original box and validate the exported scene package."""
import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
import json
import zipfile
import trimesh
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.pipeline.full_pipeline import run_mesh_pipeline
p = argparse.ArgumentParser()
p.add_argument("--output", type=Path, default=Path("backend/outputs/synthetic-demo"))
args = p.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
source = args.output / "original-box.obj"
trimesh.creation.box(extents=(1.0, 0.8, 0.6)).export(source)
result = run_mesh_pipeline(source, "synthetic-demo", args.output, {"source_type": "mesh", "filename": source.name, "origin": "original trimesh primitive"})
ET.parse(result.package_dir / "scene.xml")
ET.parse(result.package_dir / "scene.urdf")
json.loads((result.package_dir / "scene.json").read_text())
assert result.validation_report["valid"]
with zipfile.ZipFile(result.package_zip) as z:
    assert z.testzip() is None
    assert all(not Path(name).is_absolute() and ".." not in Path(name).parts for name in z.namelist())
print(f"PASS: original synthetic mesh, XML / URDF / JSON and ZIP: {result.package_zip}")
