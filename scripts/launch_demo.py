"""Run original synthetic geometry through the real HTTP API and worker.

Start an isolated API/worker first; this script never replaces application data
or simulates a capture session. Output is expressly not a reconstruction demo.
"""

import argparse
import hashlib
import io
import json
import time
import zipfile
from pathlib import Path

import httpx
import trimesh


def geometry() -> trimesh.Trimesh:
    base = trimesh.creation.box(extents=(2.8, 2.0, 0.18))
    base.apply_translation((0, 0, 0.09))
    ring = trimesh.creation.torus(major_radius=0.50, minor_radius=0.16)
    ring.apply_translation((-0.65, 0, 0.34))
    sphere = trimesh.creation.icosphere(subdivisions=3, radius=0.40)
    sphere.apply_translation((0.65, 0.25, 0.58))
    post = trimesh.creation.cylinder(radius=0.22, height=0.70, sections=48)
    post.apply_translation((0.60, -0.60, 0.53))
    return trimesh.util.concatenate([base, ring, sphere, post])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:8010")
    parser.add_argument("--output", type=Path, default=Path("artifacts/launch"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source = args.output / "original-geometry.obj"
    geometry().export(source)
    started = time.monotonic()
    with httpx.Client(base_url=args.api, timeout=30) as client:
        response = client.post("/api/projects", json={
            "name": "原创几何测试资产",
            "description": "Synthetic geometry; not a phone scan or video reconstruction",
            "source_type": "mesh",
        })
        response.raise_for_status()
        project = response.json()
        prefix = f"/api/projects/{project['id']}"
        with source.open("rb") as stream:
            response = client.post(prefix + "/upload", data={"source_type": "mesh"},
                                   files={"files": (source.name, stream, "text/plain")})
        response.raise_for_status()
        uploads = response.json()["files"]
        response = client.post(prefix + "/run", json={
            "source_type": "mesh", "uploaded_file_ids": [item["id"] for item in uploads],
        })
        response.raise_for_status()
        job = response.json()
        deadline = time.monotonic() + 120
        while job["status"] in {"queued", "running"} and time.monotonic() < deadline:
            time.sleep(0.5)
            response = client.get(f"/api/jobs/{job['id']}")
            response.raise_for_status()
            job = response.json()
        if job["status"] != "completed":
            raise RuntimeError(f"Real worker did not complete: {job}")
        response = client.post(prefix + "/validate")
        response.raise_for_status()
        validation = response.json()
        if not validation["valid"]:
            raise RuntimeError(f"Invalid package: {validation}")
        response = client.get(prefix + "/download")
        response.raise_for_status()
        package = response.content
        with zipfile.ZipFile(io.BytesIO(package)) as archive:
            if archive.testzip() is not None:
                raise RuntimeError("Corrupt archive")
            entries = archive.namelist()
            if any(Path(name).is_absolute() or ".." in Path(name).parts for name in entries):
                raise RuntimeError("Unsafe archive path")
        (args.output / "original-geometry-motrix.zip").write_bytes(package)
        evidence = {
            "provenance": "original synthetic trimesh geometry; not reconstructed",
            "project_id": project["id"], "job_id": job["id"], "status": job["status"],
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "validation": validation, "package_entries": entries,
            "package_sha256": hashlib.sha256(package).hexdigest(),
        }
        (args.output / "evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
