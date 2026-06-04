import importlib
from pathlib import Path

import trimesh
from fastapi.testclient import TestClient


def build_client(tmp_path: Path) -> TestClient:
    from app import main
    from app import settings as settings_module

    test_settings = settings_module.Settings(
        database_path=tmp_path / "real2motrix.sqlite3",
        data_dir=tmp_path / "data",
        output_dir=tmp_path / "outputs",
        cors_origins=["http://localhost:5173"],
    )
    importlib.reload(main)
    return TestClient(main.create_app(test_settings))


def test_project_upload_and_job_lifecycle(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project_response = client.post(
        "/api/projects",
        json={"name": "Lab scan", "description": "Desk corner", "source_type": "mesh"},
    )
    assert project_response.status_code == 201
    project = project_response.json()

    mesh_path = tmp_path / "fixture.obj"
    trimesh.creation.icosphere(subdivisions=1, radius=0.2).export(mesh_path)

    with mesh_path.open("rb") as mesh_file:
        upload_response = client.post(
            f"/api/projects/{project['id']}/upload",
            data={"source_type": "mesh"},
            files={"files": ("fixture.obj", mesh_file, "model/obj")},
        )
    assert upload_response.status_code == 201
    uploaded = upload_response.json()["files"][0]
    assert uploaded["filename"] == "fixture.obj"

    run_response = client.post(
        f"/api/projects/{project['id']}/run",
        json={"source_type": "mesh", "uploaded_file_ids": [uploaded["id"]]},
    )
    assert run_response.status_code == 201
    job = run_response.json()

    job_response = client.get(f"/api/jobs/{job['id']}")
    assert job_response.status_code == 200
    assert job_response.json()["status"] == "queued"

    logs_response = client.get(f"/api/jobs/{job['id']}/logs")
    assert logs_response.status_code == 200
    assert logs_response.json()["logs"] == []


def test_project_update_delete_and_regenerate(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project_response = client.post(
        "/api/projects",
        json={"name": "First task", "description": "Original", "source_type": "mesh"},
    )
    assert project_response.status_code == 201
    project = project_response.json()

    update_response = client.patch(
        f"/api/projects/{project['id']}",
        json={"name": "Edited task", "description": "Ready to rerun", "source_type": "video"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "Edited task"
    assert updated["description"] == "Ready to rerun"
    assert updated["source_type"] == "video"

    mesh_path = tmp_path / "fixture.obj"
    trimesh.creation.icosphere(subdivisions=1, radius=0.2).export(mesh_path)
    with mesh_path.open("rb") as mesh_file:
        upload_response = client.post(
            f"/api/projects/{project['id']}/upload",
            data={"source_type": "mesh"},
            files={"files": ("fixture.obj", mesh_file, "model/obj")},
        )
    assert upload_response.status_code == 201
    uploaded = upload_response.json()["files"][0]

    run_response = client.post(
        f"/api/projects/{project['id']}/run",
        json={"source_type": "mesh", "uploaded_file_ids": [uploaded["id"]]},
    )
    assert run_response.status_code == 201
    first_job = run_response.json()

    regenerate_response = client.post(f"/api/projects/{project['id']}/regenerate")
    assert regenerate_response.status_code == 201
    regenerated = regenerate_response.json()
    assert regenerated["id"] != first_job["id"]
    assert regenerated["status"] == "queued"
    assert regenerated["source_type"] == "mesh"
    assert regenerated["input_path"] == first_job["input_path"]
    assert regenerated["params_json"]["uploaded_file_ids"] == [uploaded["id"]]

    delete_response = client.delete(f"/api/projects/{project['id']}")
    assert delete_response.status_code == 204
    assert client.get(f"/api/projects/{project['id']}").status_code == 404
