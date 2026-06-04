from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.deps import get_db, get_settings_from_app
from app.database import Database
from app.pipeline.motrix.validate import validate_package
from app.services.asset_service import list_assets
from app.services.project_service import get_project
from app.settings import Settings

router = APIRouter(prefix="/api/projects/{project_id}", tags=["assets"])


@router.get("/assets")
def get_assets(project_id: str, db: Database = Depends(get_db)):
    try:
        get_project(db, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="project not found") from None
    return {"assets": list_assets(db, project_id)}


@router.get("/preview/visual")
def preview_visual(project_id: str, settings: Settings = Depends(get_settings_from_app)):
    return _file_response(settings.output_dir / project_id / "motrix_scene" / "meshes" / "scene_visual.obj")


@router.get("/preview/collision")
def preview_collision(project_id: str, settings: Settings = Depends(get_settings_from_app)):
    return _file_response(settings.output_dir / project_id / "motrix_scene" / "meshes" / "scene_collision.obj")


@router.get("/download")
def download_package(project_id: str, settings: Settings = Depends(get_settings_from_app)):
    return _file_response(settings.output_dir / project_id / "motrix_scene.zip", filename="motrix_scene.zip")


@router.post("/validate")
def validate_project(project_id: str, settings: Settings = Depends(get_settings_from_app)):
    package_dir = settings.output_dir / project_id / "motrix_scene"
    if not package_dir.exists():
        raise HTTPException(status_code=404, detail="motrix_scene output not found")
    return validate_package(package_dir)


def _file_response(path: Path, filename: str = None):
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"file not found: {path.name}")
    return FileResponse(path, filename=filename or path.name)

