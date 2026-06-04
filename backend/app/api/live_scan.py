from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import get_db
from app.database import Database
from app.schemas import LiveScanSessionCreate
from app.services.live_scan_service import (
    add_live_frame,
    add_live_mesh_chunk,
    create_live_session,
    finish_live_session,
    get_live_session,
    list_live_sessions,
    parse_json_object,
)
from app.services.project_service import get_project

router = APIRouter(prefix="/api/projects/{project_id}/live-sessions", tags=["live-scan"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_live_scan_session_route(
    project_id: str,
    payload: LiveScanSessionCreate,
    db: Database = Depends(get_db),
):
    try:
        project = get_project(db, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="project not found") from None
    return create_live_session(
        db=db,
        project=project,
        capture_type=payload.capture_type,
        capture_mode=payload.capture_mode,
        target_type=payload.target_type,
        device_model=payload.device_model,
        has_lidar=payload.has_lidar,
    )


@router.get("")
def list_live_scan_sessions_route(project_id: str, db: Database = Depends(get_db)):
    try:
        get_project(db, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="project not found") from None
    return {"live_sessions": list_live_sessions(db, project_id)}


@router.get("/{session_id}")
def get_live_scan_session_route(project_id: str, session_id: str, db: Database = Depends(get_db)):
    session = session_for_project(db, project_id, session_id)
    return session


@router.post("/{session_id}/frames", status_code=status.HTTP_201_CREATED)
def add_live_scan_frame_route(
    project_id: str,
    session_id: str,
    frame_index: int = Form(...),
    timestamp: float = Form(...),
    pose_json: str = Form("{}"),
    quality_json: str = Form("{}"),
    intrinsics_json: str = Form("{}"),
    frame: UploadFile = File(...),
    depth: Optional[UploadFile] = File(None),
    db: Database = Depends(get_db),
):
    session_for_project(db, project_id, session_id)
    try:
        pose = parse_json_object(pose_json, "pose_json")
        quality = parse_json_object(quality_json, "quality_json")
        intrinsics = parse_json_object(intrinsics_json, "intrinsics_json")
        return add_live_frame(
            db=db,
            session_id=session_id,
            frame_index=frame_index,
            timestamp=timestamp,
            pose=pose,
            quality=quality,
            intrinsics=intrinsics,
            frame_file=frame.file,
            frame_filename=frame.filename or "frame.jpg",
            depth_file=depth.file if depth else None,
            depth_filename=depth.filename if depth else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{session_id}/mesh-chunks", status_code=status.HTTP_201_CREATED)
def add_live_scan_mesh_chunk_route(
    project_id: str,
    session_id: str,
    chunk_index: int = Form(0),
    mesh: UploadFile = File(...),
    db: Database = Depends(get_db),
):
    session_for_project(db, project_id, session_id)
    try:
        return add_live_mesh_chunk(
            db=db,
            session_id=session_id,
            chunk_index=chunk_index,
            mesh_file=mesh.file,
            mesh_filename=mesh.filename or "mesh.obj",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{session_id}/preview.obj")
def get_live_scan_preview_route(project_id: str, session_id: str, db: Database = Depends(get_db)):
    session = session_for_project(db, project_id, session_id)
    preview_path = session.get("preview_path")
    if not preview_path or not Path(preview_path).exists():
        raise HTTPException(status_code=404, detail="live preview not found")
    return FileResponse(preview_path, media_type="model/obj", filename="live_scan_preview.obj")


@router.post("/{session_id}/finish", status_code=status.HTTP_201_CREATED)
def finish_live_scan_session_route(project_id: str, session_id: str, db: Database = Depends(get_db)):
    try:
        project = get_project(db, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="project not found") from None
    try:
        session_for_project(db, project_id, session_id)
        return finish_live_session(db, project, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def session_for_project(db: Database, project_id: str, session_id: str):
    try:
        get_project(db, project_id)
        session = get_live_session(db, session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="live scan session not found") from None
    if session["project_id"] != project_id:
        raise HTTPException(status_code=404, detail="live scan session not found")
    return session
