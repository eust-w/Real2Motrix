from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import get_db
from app.database import Database
from app.services.capture_session_service import create_capture_session
from app.services.job_service import create_job
from app.services.project_service import get_project
from app.services.storage_service import copy_upload_file, safe_filename

router = APIRouter(prefix="/api/projects/{project_id}", tags=["capture-sessions"])


@router.post("/capture-sessions", status_code=status.HTTP_201_CREATED)
def upload_capture_session(
    project_id: str,
    capture_type: str = Form("scene"),
    capture_mode: str = Form("arkit_pose"),
    device_type: str = Form("unknown"),
    has_lidar: bool = Form(False),
    file: UploadFile = File(...),
    db: Database = Depends(get_db),
):
    try:
        project = get_project(db, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="project not found") from None
    filename = safe_filename(file.filename or "capture_session.zip")
    if not filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="capture session upload must be a .zip file")
    destination = Path(project["root_dir"]) / "capture_sessions" / filename
    copy_upload_file(file, destination)
    try:
        session = create_capture_session(
            db,
            project_id=project_id,
            zip_path=destination,
            capture_type=capture_type,
            capture_mode=capture_mode,
            device_model=device_type,
            has_lidar=has_lidar,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    job = create_job(
        db,
        project_id=project_id,
        source_type="ios_capture",
        input_path=destination,
        capture_session_id=session["id"],
        params={"fast_mode": False},
    )
    return {"capture_session": session, "job": job}

