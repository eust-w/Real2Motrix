from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_db
from app.database import Database
from app.schemas import RunRequest
from app.services.file_service import get_uploaded_file
from app.services.job_service import create_job, get_job, list_job_logs
from app.services.project_service import get_project

router = APIRouter(prefix="/api", tags=["jobs"])


@router.post("/projects/{project_id}/run", status_code=status.HTTP_201_CREATED)
def run_project(project_id: str, payload: RunRequest, db: Database = Depends(get_db)):
    try:
        get_project(db, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="project not found") from None
    input_path = None
    uploaded_paths = []
    if payload.uploaded_file_ids:
        for uploaded_id in payload.uploaded_file_ids:
            try:
                record = get_uploaded_file(db, uploaded_id)
            except KeyError:
                raise HTTPException(status_code=404, detail="uploaded file not found") from None
            if record["project_id"] != project_id:
                raise HTTPException(status_code=400, detail="uploaded file belongs to another project")
            uploaded_paths.append(Path(record["path"]))
        input_path = uploaded_paths[0].parent if payload.source_type == "images" else uploaded_paths[0]
    job = create_job(
        db,
        project_id=project_id,
        source_type=payload.source_type,
        input_path=input_path,
        params={
            "uploaded_file_ids": payload.uploaded_file_ids,
            "uploaded_paths": [str(path) for path in uploaded_paths],
            "fast_mode": payload.fast_mode,
        },
    )
    return job


@router.get("/jobs/{job_id}")
def get_job_route(job_id: str, db: Database = Depends(get_db)):
    try:
        return get_job(db, job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="job not found") from None


@router.get("/jobs/{job_id}/logs")
def get_job_logs_route(job_id: str, db: Database = Depends(get_db)):
    try:
        get_job(db, job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="job not found") from None
    return {"logs": list_job_logs(db, job_id)}
