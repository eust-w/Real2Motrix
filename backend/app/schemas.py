from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    source_type: str = "ios_capture"


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    source_type: Optional[str] = None


class ProjectOut(BaseModel):
    id: str
    name: str
    description: str
    source_type: str
    status: str
    root_dir: str
    created_at: str
    updated_at: str


class CaptureSessionOut(BaseModel):
    id: str
    project_id: str
    capture_type: str
    capture_mode: str
    device_model: str
    has_lidar: bool
    has_depth: bool
    has_arkit_pose: bool
    zip_path: str
    metadata_json: Dict[str, Any]
    quality_json: Dict[str, Any]
    created_at: str


class LiveScanSessionCreate(BaseModel):
    capture_type: str = "scene"
    capture_mode: str = "arkit_pose"
    target_type: str = "scene"
    device_model: str = "unknown"
    has_lidar: bool = False


class LiveScanSessionOut(BaseModel):
    id: str
    project_id: str
    status: str
    capture_type: str
    capture_mode: str
    target_type: str
    device_model: str
    has_lidar: bool
    root_dir: str
    frame_count: int
    depth_frame_count: int
    mesh_chunk_count: int
    coverage_json: Dict[str, Any]
    quality_json: Dict[str, Any]
    last_pose_json: Dict[str, Any]
    preview_path: Optional[str]
    archive_path: Optional[str]
    created_at: str
    updated_at: str
    finished_at: Optional[str]


class UploadedFileOut(BaseModel):
    id: str
    project_id: str
    filename: str
    path: str
    file_type: str
    size: int
    created_at: str


class UploadResponse(BaseModel):
    files: List[UploadedFileOut]


class RunRequest(BaseModel):
    source_type: str
    uploaded_file_ids: List[str] = Field(default_factory=list)
    fast_mode: bool = False


class JobOut(BaseModel):
    id: str
    project_id: str
    capture_session_id: Optional[str]
    status: str
    progress: float
    current_step: str
    error_message: Optional[str]
    source_type: str
    input_path: Optional[str]
    params_json: Dict[str, Any]
    created_at: str
    started_at: Optional[str]
    finished_at: Optional[str]


class JobLogsOut(BaseModel):
    logs: List[Dict[str, Any]]


class AssetOut(BaseModel):
    id: str
    project_id: str
    asset_type: str
    path: str
    metadata_json: Dict[str, Any]
    created_at: str


class HealthOut(BaseModel):
    ok: bool
    database: str
    dependencies: Dict[str, Dict[str, Any]]
