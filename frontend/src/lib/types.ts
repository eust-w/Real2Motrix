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

