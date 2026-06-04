export type Project = {
  id: string;
  name: string;
  description: string;
  source_type: string;
  status: string;
  root_dir: string;
  created_at: string;
  updated_at: string;
  capture_sessions?: CaptureSession[];
  live_sessions?: LiveScanSession[];
  uploaded_files?: UploadedFile[];
  jobs?: Job[];
};

export type UploadedFile = {
  id: string;
  project_id: string;
  filename: string;
  path: string;
  file_type: string;
  size: number;
  created_at: string;
};

export type CaptureSession = {
  id: string;
  project_id: string;
  capture_type: string;
  capture_mode: string;
  device_model: string;
  has_lidar: boolean;
  has_depth: boolean;
  has_arkit_pose: boolean;
  created_at: string;
  metadata_json: Record<string, unknown>;
  quality_json: Record<string, unknown>;
};

export type LiveScanCell = {
  ix: number;
  iz: number;
  x: number;
  z: number;
  count: number;
};

export type LiveScanPoint = {
  x: number;
  y: number;
  z: number;
};

export type LiveScanCoverage = {
  coverage_score: number;
  covered_cell_count: number;
  target_cell_count: number;
  cell_size_m: number;
  bounds: { min_x: number; max_x: number; min_z: number; max_z: number } | null;
  cells: LiveScanCell[];
  weak_cells: LiveScanCell[];
  camera_path: LiveScanPoint[];
  last_position: LiveScanPoint | null;
};

export type LiveScanQuality = {
  frame_count: number;
  average_brightness: number;
  average_blur_score: number;
  tracking_lost_count: number;
  warnings: string[];
};

export type LiveScanSession = {
  id: string;
  project_id: string;
  status: "running" | "completed" | "failed" | string;
  capture_type: string;
  capture_mode: string;
  target_type: string;
  device_model: string;
  has_lidar: boolean;
  root_dir: string;
  frame_count: number;
  depth_frame_count: number;
  mesh_chunk_count: number;
  coverage_json: LiveScanCoverage;
  quality_json: LiveScanQuality;
  last_pose_json: Record<string, unknown>;
  preview_path: string | null;
  archive_path: string | null;
  created_at: string;
  updated_at: string;
  finished_at: string | null;
};

export type LiveScanCreateRequest = {
  capture_type: string;
  capture_mode: string;
  target_type: string;
  device_model: string;
  has_lidar: boolean;
};

export type Job = {
  id: string;
  project_id: string;
  capture_session_id: string | null;
  status: "queued" | "running" | "completed" | "failed";
  progress: number;
  current_step: string;
  error_message: string | null;
  source_type: string;
  input_path: string | null;
  params_json: Record<string, unknown>;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
};

export type JobLog = {
  id: number;
  job_id: string;
  level: string;
  message: string;
  created_at: string;
};

export type Asset = {
  id: string;
  project_id: string;
  asset_type: string;
  path: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type Health = {
  ok: boolean;
  database: string;
  dependencies: Record<string, { available: boolean; executable: string | null; version: string | null }>;
};
