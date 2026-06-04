from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assets, capture_sessions, files, health, jobs, projects, uploads
from app.database import Database
from app.settings import Settings, get_settings


def create_app(settings: Settings = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(title="Real2Motrix API", version="0.1.0")
    app.state.settings = resolved_settings
    app.state.db = Database(resolved_settings.database_path)
    resolved_settings.data_dir.mkdir(parents=True, exist_ok=True)
    resolved_settings.output_dir.mkdir(parents=True, exist_ok=True)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(projects.router)
    app.include_router(uploads.router)
    app.include_router(capture_sessions.router)
    app.include_router(jobs.router)
    app.include_router(assets.router)
    app.include_router(files.router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)

