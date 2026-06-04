import json
from pathlib import Path

from tests.test_api import build_client


def test_live_scan_streams_frames_updates_coverage_and_creates_rebuild_job(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    project_response = client.post(
        "/api/projects",
        json={"name": "Live hallway", "description": "continuous scan", "source_type": "ios_capture"},
    )
    assert project_response.status_code == 201
    project = project_response.json()

    start_response = client.post(
        f"/api/projects/{project['id']}/live-sessions",
        json={
            "capture_type": "scene",
            "capture_mode": "arkit_pose",
            "device_model": "iPhone",
            "has_lidar": True,
            "target_type": "scene",
        },
    )
    assert start_response.status_code == 201
    session = start_response.json()
    assert session["status"] == "running"
    assert session["frame_count"] == 0

    frame_payloads = [
        (1, {"position": [0.0, 0.0, 0.0], "quaternion": [0.0, 0.0, 0.0, 1.0]}),
        (2, {"position": [1.2, 0.0, 0.8], "quaternion": [0.0, 0.0, 0.0, 1.0]}),
    ]
    for index, pose in frame_payloads:
        frame_response = client.post(
            f"/api/projects/{project['id']}/live-sessions/{session['id']}/frames",
            data={
                "frame_index": str(index),
                "timestamp": f"100.{index}",
                "pose_json": json.dumps(pose),
                "quality_json": json.dumps({"brightness": 0.42, "blur_score": 31.0, "tracking_state": "normal"}),
                "intrinsics_json": json.dumps({"fx": 650, "fy": 650, "cx": 320, "cy": 240, "width": 640, "height": 480}),
            },
            files={"frame": (f"frame_{index:06d}.jpg", b"\xff\xd8\xff\xd9", "image/jpeg")},
        )
        assert frame_response.status_code == 201

    detail_response = client.get(f"/api/projects/{project['id']}/live-sessions/{session['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["frame_count"] == 2
    assert detail["coverage_json"]["covered_cell_count"] >= 2
    assert detail["coverage_json"]["coverage_score"] > 0
    assert detail["coverage_json"]["weak_cells"]
    assert detail["quality_json"]["average_brightness"] == 0.42

    mesh_response = client.post(
        f"/api/projects/{project['id']}/live-sessions/{session['id']}/mesh-chunks",
        data={"chunk_index": "0"},
        files={"mesh": ("mesh.obj", b"v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n", "model/obj")},
    )
    assert mesh_response.status_code == 201
    assert mesh_response.json()["mesh_chunk_count"] == 1

    preview_response = client.get(f"/api/projects/{project['id']}/live-sessions/{session['id']}/preview.obj")
    assert preview_response.status_code == 200
    assert "v 0.000000 0.000000 0.000000" in preview_response.text
    assert "l 1 2" in preview_response.text
    assert "f " in preview_response.text

    finish_response = client.post(f"/api/projects/{project['id']}/live-sessions/{session['id']}/finish")
    assert finish_response.status_code == 201
    finished = finish_response.json()
    assert finished["live_session"]["status"] == "completed"
    assert finished["job"]["status"] == "queued"
    assert finished["job"]["source_type"] == "ios_capture"
    assert finished["job"]["input_path"].endswith("live_capture.zip")
