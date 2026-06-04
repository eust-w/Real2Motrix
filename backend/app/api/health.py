from fastapi import APIRouter, Depends

from app.api.deps import get_db
from app.database import Database
from app.pipeline.utils.dependencies import inspect_dependencies

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(db: Database = Depends(get_db)):
    db.fetch_one("SELECT 1 AS ok")
    return {"ok": True, "database": str(db.path), "dependencies": inspect_dependencies()}

