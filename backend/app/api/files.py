from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.deps import get_settings_from_app
from app.services.storage_service import ensure_relative_child
from app.settings import Settings

router = APIRouter(prefix="/api/projects/{project_id}", tags=["files"])


@router.get("/files/{path:path}")
def get_project_file(project_id: str, path: str, settings: Settings = Depends(get_settings_from_app)):
    roots = [settings.data_dir / project_id, settings.output_dir / project_id]
    for root in roots:
        try:
            candidate = ensure_relative_child(root, path)
        except ValueError:
            raise HTTPException(status_code=400, detail="path traversal is not allowed") from None
        if candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
    raise HTTPException(status_code=404, detail="file not found")

