import { useEffect, useMemo, useState } from "react";
import {
  Box,
  Download,
  FolderPlus,
  HardDrive,
  Languages,
  Play,
  RefreshCw,
  RotateCw,
  Save,
  Search,
  Settings,
  Trash2,
  Upload
} from "lucide-react";
import { api } from "./lib/api";
import type { Asset, Health, Job, JobLog, LiveScanSession, Project, UploadedFile } from "./lib/types";
import {
  createTranslator,
  localeLabels,
  nextLocale,
  readStoredLocale,
  type Locale,
  type Translator
} from "./lib/i18n";
import { MeshPreview, type PreviewMode, type PreviewObjectAsset, type PreviewStats } from "./components/MeshPreview";
import { JobProgress } from "./components/JobProgress";
import { JobLogs } from "./components/JobLogs";
import { AssetTree } from "./components/AssetTree";
import { DependencyStatus } from "./components/DependencyStatus";
import { ValidationReport } from "./components/ValidationReport";
import { LiveScanPanel, type LiveTargetType } from "./components/LiveScanPanel";

const sourceTypes = ["mesh", "ios_capture", "images", "video", "pointcloud", "polycam", "scaniverse", "nerfstudio"];

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [logs, setLogs] = useState<JobLog[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [liveSessions, setLiveSessions] = useState<LiveScanSession[]>([]);
  const [liveSession, setLiveSession] = useState<LiveScanSession | null>(null);
  const [liveTargetType, setLiveTargetType] = useState<LiveTargetType>("scene");
  const [taskQuery, setTaskQuery] = useState("");
  const [sourceType, setSourceType] = useState("mesh");
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editSourceType, setEditSourceType] = useState("mesh");
  const [uploadedIds, setUploadedIds] = useState<string[]>([]);
  const [validation, setValidation] = useState<Record<string, unknown> | null>(null);
  const [previewMode, setPreviewMode] = useState<PreviewMode>("scene");
  const [previewAssetId, setPreviewAssetId] = useState<string | null>(null);
  const [locale, setLocale] = useState<Locale>(() => readStoredLocale());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const t = useMemo(() => createTranslator(locale), [locale]);
  const activeJob = useMemo(() => jobs[0] ?? null, [jobs]);
  const activeLiveSession = liveSession ?? liveSessions[0] ?? null;
  const filteredProjects = useMemo(() => {
    const query = taskQuery.trim().toLowerCase();
    if (!query) return projects;
    return projects.filter((item) =>
      [item.name, item.description, item.source_type, item.status].some((value) => value.toLowerCase().includes(query))
    );
  }, [projects, taskQuery]);
  const selectedPreviewAsset = useMemo(
    () => assets.find((asset) => asset.id === previewAssetId) ?? null,
    [assets, previewAssetId]
  );
  const previewConfig = useMemo(
    () => (project ? buildPreviewConfig(project.id, assets, selectedPreviewAsset, t) : null),
    [project?.id, assets, selectedPreviewAsset, t]
  );

  useEffect(() => {
    if (!project) {
      setEditName("");
      setEditDescription("");
      setEditSourceType("mesh");
      return;
    }
    setEditName(project.name);
    setEditDescription(project.description);
    setEditSourceType(project.source_type);
    setSourceType(project.source_type);
  }, [project?.id, project?.name, project?.description, project?.source_type]);

  async function refresh(preferredId: string | null | undefined = selectedId) {
    setError(null);
    try {
      const [nextHealth, nextProjects] = await Promise.all([api.health(), api.listProjects()]);
      setHealth(nextHealth);
      setProjects(nextProjects);
      const projectId =
        preferredId && nextProjects.some((item) => item.id === preferredId) ? preferredId : nextProjects[0]?.id ?? null;
      setSelectedId(projectId);
      if (projectId) {
        const detail = await api.getProject(projectId);
        const nextAssets = await api.listAssets(projectId);
        const nextLiveSessions = detail.live_sessions ?? [];
        setProject(detail);
        setJobs(detail.jobs ?? []);
        setAssets(nextAssets);
        setLiveSessions(nextLiveSessions);
        setLiveSession((current) => {
          if (current) {
            return nextLiveSessions.find((item) => item.id === current.id) ?? nextLiveSessions[0] ?? null;
          }
          return nextLiveSessions[0] ?? null;
        });
        setSourceType(detail.source_type);
        if (detail.uploaded_files?.length) {
          setUploadedIds([detail.uploaded_files[0].id]);
        } else {
          setUploadedIds([]);
        }
      } else {
        setProject(null);
        setJobs([]);
        setLogs([]);
        setAssets([]);
        setLiveSessions([]);
        setLiveSession(null);
        setUploadedIds([]);
        setValidation(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  useEffect(() => {
    if (!activeJob || !["queued", "running"].includes(activeJob.status)) return undefined;
    const timer = window.setInterval(async () => {
      const job = await api.getJob(activeJob.id);
      const nextLogs = await api.getJobLogs(activeJob.id);
      setJobs((current) => [job, ...current.filter((item) => item.id !== job.id)]);
      setLogs(nextLogs);
      if (job.status === "completed" && selectedId) {
        setAssets(await api.listAssets(selectedId));
      }
    }, 2000);
    return () => window.clearInterval(timer);
  }, [activeJob?.id, activeJob?.status, selectedId]);

  useEffect(() => {
    if (!project || !liveSession || liveSession.status !== "running") return undefined;
    const timer = window.setInterval(async () => {
      try {
        const next = await api.getLiveSession(project.id, liveSession.id);
        setLiveSession(next);
        setLiveSessions((current) => [next, ...current.filter((item) => item.id !== next.id)]);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      }
    }, 2000);
    return () => window.clearInterval(timer);
  }, [project?.id, liveSession?.id, liveSession?.status]);

  useEffect(() => {
    if (previewAssetId && !assets.some((asset) => asset.id === previewAssetId)) {
      setPreviewAssetId(null);
    }
  }, [assets, previewAssetId]);

  async function createProject(formData: FormData) {
    setBusy(true);
    try {
      const created = await api.createProject({
        name: String(formData.get("name") ?? "Untitled"),
        description: String(formData.get("description") ?? ""),
        source_type: String(formData.get("source_type") ?? "mesh")
      });
      setSelectedId(created.id);
      await refresh(created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function upload(files: FileList | null) {
    if (!project || !files?.length) return;
    setBusy(true);
    try {
      const response = await api.uploadFiles(project.id, sourceType, files);
      setUploadedIds(response.files.map((file: UploadedFile) => file.id));
      await refresh(project.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function run() {
    if (!project) return;
    setBusy(true);
    try {
      const job = await api.runProject(project.id, sourceType, uploadedIds);
      setJobs((current) => [job, ...current]);
      setLogs([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function updateTask(formData: FormData) {
    if (!project) return;
    setBusy(true);
    try {
      const updated = await api.updateProject(project.id, {
        name: String(formData.get("name") ?? project.name),
        description: String(formData.get("description") ?? ""),
        source_type: String(formData.get("source_type") ?? project.source_type)
      });
      setProject((current) => (current ? { ...current, ...updated } : updated));
      setSourceType(updated.source_type);
      await refresh(updated.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function deleteTask() {
    if (!project) return;
    setBusy(true);
    try {
      await api.deleteProject(project.id);
      setSelectedId(null);
      setProject(null);
      setJobs([]);
      setLogs([]);
      setAssets([]);
      setLiveSessions([]);
      setLiveSession(null);
      setUploadedIds([]);
      setValidation(null);
      await refresh(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function regenerateTask() {
    if (!project) return;
    setBusy(true);
    try {
      const job = await api.regenerateProject(project.id);
      setJobs((current) => [job, ...current]);
      setLogs([]);
      setSourceType(job.source_type);
      await refresh(project.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function validate() {
    if (!project) return;
    try {
      setValidation(await api.validate(project.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function createLiveScanSession() {
    if (!project) return;
    setBusy(true);
    try {
      const session = await api.createLiveSession(project.id, {
        capture_type: liveTargetType === "object" ? "object" : "scene",
        capture_mode: "arkit_pose",
        target_type: liveTargetType,
        device_model: "desktop_browser",
        has_lidar: false
      });
      setLiveSession(session);
      setLiveSessions((current) => [session, ...current.filter((item) => item.id !== session.id)]);
      await refresh(project.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function refreshLiveScanSession() {
    if (!project) return;
    try {
      if (liveSession) {
        const next = await api.getLiveSession(project.id, liveSession.id);
        setLiveSession(next);
        setLiveSessions((current) => [next, ...current.filter((item) => item.id !== next.id)]);
        return;
      }
      const nextSessions = await api.listLiveSessions(project.id);
      setLiveSessions(nextSessions);
      setLiveSession(nextSessions[0] ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function finishLiveScanSession() {
    if (!project || !liveSession) return;
    setBusy(true);
    try {
      const response = await api.finishLiveSession(project.id, liveSession.id);
      setLiveSession(response.live_session);
      setLiveSessions((current) => [response.live_session, ...current.filter((item) => item.id !== response.live_session.id)]);
      setJobs((current) => [response.job, ...current.filter((item) => item.id !== response.job.id)]);
      setLogs([]);
      await refresh(project.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  function switchLocale() {
    setLocale((current) => {
      const next = nextLocale(current);
      window.localStorage.setItem("real2motrix.locale", next);
      return next;
    });
  }

  const alternateLocale = nextLocale(locale);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Box size={26} />
          <div>
            <strong>Real2Motrix</strong>
            <span>{t("brand.subtitle")}</span>
          </div>
        </div>
        <form className="new-project" action={createProject}>
          <div className="section-title">
            <FolderPlus size={16} />
            {t("newProject.title")}
          </div>
          <input name="name" placeholder={t("form.projectName")} required />
          <input name="description" placeholder={t("form.description")} />
          <select name="source_type" defaultValue="mesh">
            {sourceTypes.map((type) => (
              <option key={type} value={type}>
                {sourceTypeLabel(type, t)}
              </option>
            ))}
          </select>
          <button disabled={busy}>
            <FolderPlus size={15} />
            {t("actions.create")}
          </button>
        </form>
        <div className="project-list">
          <div className="section-title">
            <HardDrive size={16} />
            {t("projects.title")}
          </div>
          <label className="project-search">
            <Search size={14} />
            <input value={taskQuery} onChange={(event) => setTaskQuery(event.target.value)} placeholder={t("projects.search")} />
          </label>
          {filteredProjects.length === 0 ? <p className="empty">{t("projects.empty")}</p> : null}
          {filteredProjects.map((item) => (
            <button
              className={item.id === selectedId ? "project-row active" : "project-row"}
              key={item.id}
              onClick={() => {
                setSelectedId(item.id);
                setPreviewMode("scene");
                setValidation(null);
                void refresh(item.id);
              }}
            >
              <span>{item.name}</span>
              <small>{statusLabel(item.status, t)}</small>
            </button>
          ))}
        </div>
        <DependencyStatus health={health} t={t} />
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <p>{t("workspace.subtitle")}</p>
            <h1>{project?.name ?? t("workspace.noProject")}</h1>
          </div>
          <div className="topbar-actions">
            <button
              className="ghost"
              aria-label={t("language.switchTo", { language: localeLabels[alternateLocale] })}
              onClick={switchLocale}
            >
              <Languages size={16} />
              {localeLabels[alternateLocale]}
            </button>
            <button className="ghost" onClick={() => void refresh()}>
              <RefreshCw size={16} />
              {t("actions.refresh")}
            </button>
          </div>
        </header>

        {error && <div className="error-banner">{error}</div>}

        <section className="grid">
          <div className="panel task-panel">
            <div className="panel-header">
              <div>
                <p>{t("task.detailsSubtitle")}</p>
                <h2>{t("task.detailsTitle")}</h2>
              </div>
              <Settings size={20} />
            </div>
            {project ? (
              <form className="task-form" action={updateTask}>
                <label className="field-label">{t("task.detailsName")}</label>
                <input name="name" value={editName} onChange={(event) => setEditName(event.target.value)} required />
                <label className="field-label">{t("task.detailsDescription")}</label>
                <input
                  name="description"
                  value={editDescription}
                  onChange={(event) => setEditDescription(event.target.value)}
                />
                <label className="field-label">{t("task.detailsSource")}</label>
                <select
                  name="source_type"
                  value={editSourceType}
                  onChange={(event) => setEditSourceType(event.target.value)}
                >
                  {sourceTypes.map((type) => (
                    <option key={type} value={type}>
                      {sourceTypeLabel(type, t)}
                    </option>
                  ))}
                </select>
                <div className="task-actions">
                  <button className="primary" disabled={busy}>
                    <Save size={16} />
                    {t("task.save")}
                  </button>
                  <button className="ghost" disabled={busy} type="button" onClick={() => void regenerateTask()}>
                    <RotateCw size={16} />
                    {t("task.regenerate")}
                  </button>
                  <button className="ghost danger" disabled={busy} type="button" onClick={() => void deleteTask()}>
                    <Trash2 size={16} />
                    {t("task.delete")}
                  </button>
                </div>
              </form>
            ) : (
              <p className="empty">{t("workspace.noProject")}</p>
            )}
          </div>

          <div className="panel upload-panel">
            <div className="panel-header">
              <div>
                <p>{t("input.subtitle")}</p>
                <h2>{t("input.title")}</h2>
              </div>
              <Upload size={20} />
            </div>
            <label className="field-label">{t("input.sourceType")}</label>
            <select value={sourceType} onChange={(event) => setSourceType(event.target.value)}>
              {sourceTypes.map((type) => (
                <option key={type} value={type}>
                  {sourceTypeLabel(type, t)}
                </option>
              ))}
            </select>
            <label className="drop-zone">
              <Upload size={22} />
              <span>{t("input.dropZone")}</span>
              <input type="file" multiple onChange={(event) => void upload(event.currentTarget.files)} />
            </label>
            <button className="primary" disabled={!project || busy || uploadedIds.length === 0} onClick={() => void run()}>
              <Play size={16} />
              {t("actions.startPipeline")}
            </button>
          </div>

          <JobProgress
            job={activeJob}
            t={t}
            formatStatus={(status) => statusLabel(status, t)}
            formatSource={(source) => sourceTypeLabel(source, t)}
          />

          <LiveScanPanel
            session={activeLiveSession}
            targetType={liveTargetType}
            previewObjUrl={project && activeLiveSession ? api.livePreviewUrl(project.id, activeLiveSession.id) : undefined}
            busy={busy || !project}
            t={t}
            onTargetTypeChange={setLiveTargetType}
            onCreate={() => void createLiveScanSession()}
            onRefresh={() => void refreshLiveScanSession()}
            onFinish={() => void finishLiveScanSession()}
          />

          <div className="panel preview-panel">
            <div className="panel-header">
              <div>
                <p>{t("preview.subtitle")}</p>
                <h2>{t("preview.title")}</h2>
              </div>
              {project && (
                <a className="download-link" href={api.downloadUrl(project.id)}>
                  <Download size={16} />
                  {t("actions.package")}
                </a>
              )}
            </div>
            {project ? (
              <MeshPreview
                visualUrl={previewConfig?.visualUrl ?? api.visualUrl(project.id)}
                collisionUrl={previewConfig?.collisionUrl ?? api.collisionUrl(project.id)}
                sceneUrl={api.sceneJsonUrl(project.id)}
                manifestUrl={api.assetManifestUrl(project.id)}
                materialUrl={api.fileUrl(project.id, "motrix_scene/meshes/material.mtl")}
                materialBaseUrl={`${api.fileUrl(project.id, "motrix_scene/meshes/material.mtl").replace(/material\\.mtl$/, "")}`}
                mode={previewMode}
                selectedLabel={previewConfig?.selectedLabel}
                selectedStats={previewConfig?.selectedStats}
                objectAssets={previewConfig?.objectAssets}
                locale={locale}
                t={t}
                onModeChange={(mode) => {
                  setPreviewMode(mode);
                  if (mode === "scene") {
                    setPreviewAssetId(null);
                  }
                }}
              />
            ) : null}
          </div>

          <AssetTree
            assets={assets}
            activeMode={previewMode}
            activeAssetId={previewAssetId}
            t={t}
            onPreview={(asset, mode) => {
              setPreviewMode(mode);
              setPreviewAssetId(asset.asset_type === "motrix_package" ? null : asset.id);
            }}
          />
          <JobLogs logs={logs} t={t} />
          <ValidationReport validation={validation} onValidate={() => void validate()} t={t} />
        </section>
      </main>
    </div>
  );
}

type PreviewConfig = {
  visualUrl: string;
  collisionUrl: string;
  selectedLabel?: string;
  selectedStats?: PreviewStats;
  objectAssets: PreviewObjectAsset[];
};

function buildPreviewConfig(projectId: string, assets: Asset[], selectedAsset: Asset | null, t: Translator): PreviewConfig {
  const objectAssets = buildObjectAssets(projectId, assets);
  let visualUrl = api.visualUrl(projectId);
  let collisionUrl = api.collisionUrl(projectId);
  let selectedLabel: string | undefined;
  let selectedStats: PreviewStats | undefined;

  if (selectedAsset) {
    const selectedUrl = api.assetFileUrl(projectId, selectedAsset.path);
    const objectId = objectIdForAsset(selectedAsset);
    const pairedObject = objectId ? objectAssets.find((asset) => asset.id === objectId) : undefined;
    selectedLabel = assetPreviewLabel(selectedAsset, t);
    selectedStats = statsFromAsset(selectedAsset);

    if (isVisualAsset(selectedAsset)) {
      visualUrl = selectedUrl;
      collisionUrl = pairedObject?.collisionUrl ?? collisionUrl;
    }
    if (isCollisionAsset(selectedAsset)) {
      collisionUrl = selectedUrl;
      visualUrl = pairedObject?.visualUrl ?? visualUrl;
    }
  }

  return { visualUrl, collisionUrl, selectedLabel, selectedStats, objectAssets };
}

function buildObjectAssets(projectId: string, assets: Asset[]): PreviewObjectAsset[] {
  const byObject = new Map<string, { id: string; label: string; visualUrl?: string; collisionUrl?: string }>();
  for (const asset of assets) {
    if (!asset.asset_type.startsWith("object_")) continue;
    const objectId = objectIdForAsset(asset);
    if (!objectId) continue;
    const item = byObject.get(objectId) ?? { id: objectId, label: objectId };
    if (asset.asset_type === "object_visual_mesh") {
      item.visualUrl = api.assetFileUrl(projectId, asset.path);
    }
    if (asset.asset_type === "object_collision_mesh") {
      item.collisionUrl = api.assetFileUrl(projectId, asset.path);
    }
    byObject.set(objectId, item);
  }
  return Array.from(byObject.values())
    .filter((item): item is PreviewObjectAsset & { visualUrl: string } => Boolean(item.visualUrl))
    .map((item) => ({ id: item.id, label: item.label, visualUrl: item.visualUrl, collisionUrl: item.collisionUrl }));
}

function isVisualAsset(asset: Asset) {
  return asset.asset_type.endsWith("visual_mesh") || asset.asset_type === "visual_mesh";
}

function isCollisionAsset(asset: Asset) {
  return asset.asset_type.endsWith("collision_mesh") || asset.asset_type === "collision_mesh";
}

function objectIdForAsset(asset: Asset): string | null {
  const objectId = asset.metadata_json.object_id ?? asset.metadata_json.id;
  return typeof objectId === "string" ? objectId : null;
}

function assetPreviewLabel(asset: Asset, t: Translator): string {
  const objectId = objectIdForAsset(asset);
  if (objectId && asset.asset_type.startsWith("object_")) {
    return `${objectId} ${assetTypeLabel(asset.asset_type, t)}`;
  }
  return assetTypeLabel(asset.asset_type, t);
}

function statsFromAsset(asset: Asset): PreviewStats {
  const metadata = asset.metadata_json;
  return {
    visual_faces: numberMeta(metadata.visual_faces),
    collision_faces: numberMeta(metadata.collision_faces),
    bbox: boundsMeta(metadata.bbox)
  };
}

function numberMeta(value: unknown): number | undefined {
  return typeof value === "number" ? value : undefined;
}

function boundsMeta(value: unknown): number[][] | undefined {
  if (!Array.isArray(value) || value.length < 2) return undefined;
  const rows = value.filter((row): row is number[] => Array.isArray(row) && row.every((item) => typeof item === "number"));
  return rows.length >= 2 ? rows : undefined;
}

function statusLabel(status: string, t: Translator): string {
  if (status === "created") return t("status.created");
  if (status === "queued") return t("status.queued");
  if (status === "running") return t("status.running");
  if (status === "completed") return t("status.completed");
  if (status === "failed") return t("status.failed");
  return status;
}

function sourceTypeLabel(sourceType: string, t: Translator): string {
  if (sourceType === "mesh") return t("source.mesh");
  if (sourceType === "ios_capture") return t("source.ios_capture");
  if (sourceType === "images") return t("source.images");
  if (sourceType === "video") return t("source.video");
  if (sourceType === "pointcloud") return t("source.pointcloud");
  if (sourceType === "polycam") return t("source.polycam");
  if (sourceType === "scaniverse") return t("source.scaniverse");
  if (sourceType === "nerfstudio") return t("source.nerfstudio");
  return sourceType;
}

function assetTypeLabel(assetType: string, t: Translator): string {
  if (assetType === "visual_mesh") return t("assets.visualMesh");
  if (assetType === "collision_mesh") return t("assets.collisionMesh");
  if (assetType === "scene_visual_mesh") return t("assets.sceneVisualMesh");
  if (assetType === "scene_collision_mesh") return t("assets.sceneCollisionMesh");
  if (assetType === "object_visual_mesh") return t("assets.objectVisualMesh");
  if (assetType === "object_collision_mesh") return t("assets.objectCollisionMesh");
  if (assetType === "motrix_package") return t("assets.motrixPackage");
  return assetType;
}
