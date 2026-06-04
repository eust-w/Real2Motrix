import type { Asset, Health, Job, JobLog, LiveScanCreateRequest, LiveScanSession, Project, UploadedFile } from "./types";

type LocationLike = Pick<Location, "protocol" | "hostname">;

export function resolveApiBase(explicit = import.meta.env.VITE_API_BASE_URL, locationLike?: LocationLike): string {
  if (explicit) return explicit;
  const currentLocation =
    locationLike ?? (typeof globalThis.location !== "undefined" ? globalThis.location : undefined);
  if (currentLocation?.hostname) {
    return `${currentLocation.protocol}//${currentLocation.hostname}:8000`;
  }
  return "http://localhost:8000";
}

const API_BASE = resolveApiBase();

function encodeProjectPath(path: string): string {
  return path
    .split("/")
    .filter(Boolean)
    .map((part) => encodeURIComponent(part))
    .join("/");
}

function generatedAssetPath(path: string): string {
  const normalized = path.replace(/\\/g, "/");
  if (normalized.startsWith("motrix_scene/")) return normalized;
  const marker = "/motrix_scene/";
  const index = normalized.indexOf(marker);
  if (index >= 0) return `motrix_scene/${normalized.slice(index + marker.length)}`;
  return normalized.replace(/^\/+/, "");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = init ? await fetch(url, init) : await fetch(url);
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      message = body.detail ?? message;
    } catch {
      // Keep HTTP status text when the response is not JSON.
    }
    throw new Error(message);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  baseUrl: API_BASE,
  health: () => request<Health>("/api/health"),
  listProjects: async () => (await request<{ projects: Project[] }>("/api/projects")).projects,
  createProject: (payload: { name: string; description: string; source_type: string }) =>
    request<Project>("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }),
  updateProject: (projectId: string, payload: { name: string; description: string; source_type: string }) =>
    request<Project>(`/api/projects/${projectId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }),
  deleteProject: (projectId: string) =>
    request<void>(`/api/projects/${projectId}`, {
      method: "DELETE"
    }),
  regenerateProject: (projectId: string) =>
    request<Job>(`/api/projects/${projectId}/regenerate`, {
      method: "POST"
    }),
  createLiveSession: (projectId: string, payload: LiveScanCreateRequest) =>
    request<LiveScanSession>(`/api/projects/${projectId}/live-sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }),
  listLiveSessions: async (projectId: string) =>
    (await request<{ live_sessions: LiveScanSession[] }>(`/api/projects/${projectId}/live-sessions`)).live_sessions,
  getLiveSession: (projectId: string, sessionId: string) =>
    request<LiveScanSession>(`/api/projects/${projectId}/live-sessions/${sessionId}`),
  finishLiveSession: (projectId: string, sessionId: string) =>
    request<{ live_session: LiveScanSession; job: Job }>(`/api/projects/${projectId}/live-sessions/${sessionId}/finish`, {
      method: "POST"
    }),
  getProject: (projectId: string) => request<Project>(`/api/projects/${projectId}`),
  uploadFiles: async (projectId: string, sourceType: string, files: FileList) => {
    const form = new FormData();
    form.set("source_type", sourceType);
    Array.from(files).forEach((file) => form.append("files", file));
    return request<{ files: UploadedFile[] }>(`/api/projects/${projectId}/upload`, {
      method: "POST",
      body: form
    });
  },
  runProject: (projectId: string, sourceType: string, uploadedFileIds: string[]) =>
    request<Job>(`/api/projects/${projectId}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source_type: sourceType, uploaded_file_ids: uploadedFileIds })
    }),
  getJob: (jobId: string) => request<Job>(`/api/jobs/${jobId}`),
  getJobLogs: async (jobId: string) => (await request<{ logs: JobLog[] }>(`/api/jobs/${jobId}/logs`)).logs,
  listAssets: async (projectId: string) => (await request<{ assets: Asset[] }>(`/api/projects/${projectId}/assets`)).assets,
  validate: (projectId: string) => request<Record<string, unknown>>(`/api/projects/${projectId}/validate`, { method: "POST" }),
  fileUrl: (projectId: string, path: string) => `${API_BASE}/api/projects/${projectId}/files/${encodeProjectPath(path)}`,
  assetFileUrl: (projectId: string, path: string) => `${API_BASE}/api/projects/${projectId}/files/${encodeProjectPath(generatedAssetPath(path))}`,
  sceneJsonUrl: (projectId: string) => `${API_BASE}/api/projects/${projectId}/files/motrix_scene/scene.json`,
  assetManifestUrl: (projectId: string) =>
    `${API_BASE}/api/projects/${projectId}/files/motrix_scene/metadata/asset_manifest.json`,
  visualUrl: (projectId: string) => `${API_BASE}/api/projects/${projectId}/preview/visual`,
  collisionUrl: (projectId: string) => `${API_BASE}/api/projects/${projectId}/preview/collision`,
  livePreviewUrl: (projectId: string, sessionId: string) =>
    `${API_BASE}/api/projects/${projectId}/live-sessions/${sessionId}/preview.obj`,
  downloadUrl: (projectId: string) => `${API_BASE}/api/projects/${projectId}/download`
};
