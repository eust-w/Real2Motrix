from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_db, get_settings_from_app
from app.database import Database
from app.schemas import ProjectCreate
from app.services.capture_session_service import list_capture_sessions
from app.services.file_service import list_uploaded_files
from app.services.job_service import list_jobs
from app.services.project_service import create_project, delete_project, get_project, list_projects
from app.settings import Settings

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project_route(
    payload: ProjectCreate,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings_from_app),
):
    return create_project(db, settings.data_dir, payload.name, payload.description, payload.source_type)


@router.get("")
def list_projects_route(db: Database = Depends(get_db)):
    return {"projects": list_projects(db)}


@router.get("/{project_id}")
def get_project_route(project_id: str, db: Database = Depends(get_db)):
    try:
        project = get_project(db, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="project not found") from None
    project["capture_sessions"] = list_capture_sessions(db, project_id)
    project["uploaded_files"] = list_uploaded_files(db, project_id)
    project["jobs"] = list_jobs(db, project_id)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_route(project_id: str, db: Database = Depends(get_db)):
    try:
        delete_project(db, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="project not found") from None
    return None

