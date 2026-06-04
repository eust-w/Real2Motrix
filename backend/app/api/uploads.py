from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import get_db
from app.database import Database
from app.services.file_service import create_uploaded_file
from app.services.project_service import get_project
from app.services.storage_service import copy_upload_file, safe_filename

router = APIRouter(prefix="/api/projects/{project_id}", tags=["uploads"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_files(
    project_id: str,
    source_type: str = Form("mesh"),
    files: List[UploadFile] = File(...),
    db: Database = Depends(get_db),
):
    try:
        project = get_project(db, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="project not found") from None
    uploaded = []
    upload_dir = Path(project["root_dir"]) / "uploads"
    for upload in files:
        filename = safe_filename(upload.filename or "upload.bin")
        destination = upload_dir / filename
        size = copy_upload_file(upload, destination)
        uploaded.append(
            create_uploaded_file(
                db,
                project_id=project_id,
                filename=filename,
                path=destination,
                file_type=source_type,
                size=size,
            )
        )
    return {"files": uploaded}

