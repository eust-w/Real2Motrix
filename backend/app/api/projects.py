from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_db, get_settings_from_app
from app.database import Database
from app.schemas import ProjectCreate, ProjectUpdate
from app.services.capture_session_service import list_capture_sessions
from app.services.file_service import get_uploaded_file, list_uploaded_files
from app.services.job_service import create_job, list_jobs
from app.services.live_scan_service import list_live_sessions
from app.services.project_service import create_project, delete_project, get_project, list_projects, update_project, update_project_status
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
    project["live_sessions"] = list_live_sessions(db, project_id)
    project["uploaded_files"] = list_uploaded_files(db, project_id)
    project["jobs"] = list_jobs(db, project_id)
    return project


@router.patch("/{project_id}")
def update_project_route(project_id: str, payload: ProjectUpdate, db: Database = Depends(get_db)):
    try:
        return update_project(
            db,
            project_id,
            name=payload.name,
            description=payload.description,
            source_type=payload.source_type,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="project not found") from None


@router.post("/{project_id}/regenerate", status_code=status.HTTP_201_CREATED)
def regenerate_project_route(project_id: str, db: Database = Depends(get_db)):
    try:
        project = get_project(db, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="project not found") from None

    source = regeneration_source(db, project_id, project)
    if source is None:
        raise HTTPException(status_code=400, detail="no previous input available for regeneration")

    job = create_job(
        db,
        project_id=project_id,
        source_type=source["source_type"],
        input_path=source["input_path"],
        params=source["params"],
    )
    update_project_status(db, project_id, "queued")
    return job


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_route(project_id: str, db: Database = Depends(get_db)):
    try:
        delete_project(db, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="project not found") from None
    return None


def regeneration_source(db: Database, project_id: str, project: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    jobs = list_jobs(db, project_id)
    if jobs:
        latest_job = jobs[0]
        source_type = latest_job["source_type"] or project["source_type"]
        params = dict(latest_job["params_json"] or {})
        uploaded_file_ids = string_list(params.get("uploaded_file_ids"))
        if uploaded_file_ids:
            uploaded_paths = uploaded_paths_for_ids(db, project_id, uploaded_file_ids)
            return {
                "source_type": source_type,
                "input_path": input_path_for_source(source_type, uploaded_paths),
                "params": {
                    **params,
                    "uploaded_file_ids": uploaded_file_ids,
                    "uploaded_paths": [str(path) for path in uploaded_paths],
                    "regenerated_from_job_id": latest_job["id"],
                },
            }
        if latest_job["input_path"]:
            return {
                "source_type": source_type,
                "input_path": Path(latest_job["input_path"]),
                "params": {**params, "regenerated_from_job_id": latest_job["id"]},
            }

    uploads = list_uploaded_files(db, project_id)
    if not uploads:
        return None

    source_type = uploads[0]["file_type"] or project["source_type"]
    uploaded_file_ids = [upload["id"] for upload in uploads if upload["file_type"] == source_type]
    uploaded_paths = [Path(upload["path"]) for upload in uploads if upload["file_type"] == source_type]
    if not uploaded_paths:
        return None
    return {
        "source_type": source_type,
        "input_path": input_path_for_source(source_type, uploaded_paths),
        "params": {
            "uploaded_file_ids": uploaded_file_ids,
            "uploaded_paths": [str(path) for path in uploaded_paths],
            "fast_mode": False,
        },
    }


def uploaded_paths_for_ids(db: Database, project_id: str, uploaded_file_ids: List[str]) -> List[Path]:
    uploaded_paths = []
    for uploaded_id in uploaded_file_ids:
        try:
            uploaded = get_uploaded_file(db, uploaded_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="uploaded file not found") from None
        if uploaded["project_id"] != project_id:
            raise HTTPException(status_code=400, detail="uploaded file belongs to another project")
        uploaded_paths.append(Path(uploaded["path"]))
    return uploaded_paths


def input_path_for_source(source_type: str, uploaded_paths: List[Path]) -> Path:
    return uploaded_paths[0].parent if source_type == "images" else uploaded_paths[0]


def string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]
