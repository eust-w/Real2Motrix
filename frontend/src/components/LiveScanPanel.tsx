import { CheckCircle2, Radar, RefreshCw, Smartphone, Square } from "lucide-react";
import type { Translator } from "../lib/i18n";
import type { LiveScanSession } from "../lib/types";
import { LiveScanPreview } from "./LiveScanPreview";

export type LiveTargetType = "scene" | "object";

export function LiveScanPanel({
  session,
  targetType,
  previewObjUrl,
  busy,
  t,
  onTargetTypeChange,
  onCreate,
  onFinish,
  onRefresh
}: {
  session: LiveScanSession | null;
  targetType: LiveTargetType;
  previewObjUrl?: string;
  busy: boolean;
  t: Translator;
  onTargetTypeChange: (targetType: LiveTargetType) => void;
  onCreate: () => void;
  onFinish: () => void;
  onRefresh: () => void;
}) {
  const coverage = session?.coverage_json ?? null;
  const quality = session?.quality_json ?? null;
  const coveragePercent = Math.round((coverage?.coverage_score ?? 0) * 100);
  const running = session?.status === "running";

  return (
    <div className="panel live-panel">
      <div className="panel-header">
        <div>
          <p>{t("live.subtitle")}</p>
          <h2>{t("live.title")}</h2>
        </div>
        <Smartphone size={20} />
      </div>

      <div className="live-target-tabs" role="tablist" aria-label={t("live.target")}>
        <button className={targetType === "scene" ? "selected" : ""} onClick={() => onTargetTypeChange("scene")}>
          {t("live.targetScene")}
        </button>
        <button className={targetType === "object" ? "selected" : ""} onClick={() => onTargetTypeChange("object")}>
          {t("live.targetObject")}
        </button>
      </div>

      <div className="live-actions">
        <button className="primary" disabled={busy || running} onClick={onCreate}>
          <Radar size={16} />
          {t("live.create")}
        </button>
        <button className="ghost" disabled={!session || busy} onClick={onRefresh}>
          <RefreshCw size={16} />
          {t("actions.refresh")}
        </button>
        <button className="ghost" disabled={!session || !running || busy || (session?.frame_count ?? 0) === 0} onClick={onFinish}>
          <Square size={16} />
          {t("live.finish")}
        </button>
      </div>

      {session ? (
        <>
          <div className={`status-pill ${session.status}`}>{liveStatusLabel(session.status, t)}</div>
          <div className="live-preview-wrap">
            <LiveScanPreview coverage={coverage} previewObjUrl={previewObjUrl} />
          </div>
          <div className="live-meter">
            <div>
              <strong>{coveragePercent}%</strong>
              <span>{t("live.coverage")}</span>
            </div>
            <div>
              <strong>{session.frame_count}</strong>
              <span>{t("live.frames")}</span>
            </div>
            <div>
              <strong>{coverage?.weak_cells?.length ?? 0}</strong>
              <span>{t("live.weakCells")}</span>
            </div>
          </div>
          <div className="live-progress-track">
            <div style={{ width: `${Math.min(100, coveragePercent)}%` }} />
          </div>
          <dl className="details live-details">
            <dt>{t("live.device")}</dt>
            <dd>{session.device_model}</dd>
            <dt>{t("live.target")}</dt>
            <dd>{session.target_type === "object" ? t("live.targetObject") : t("live.targetScene")}</dd>
            <dt>{t("live.brightness")}</dt>
            <dd>{formatFixed(quality?.average_brightness)}</dd>
            <dt>{t("live.blur")}</dt>
            <dd>{formatFixed(quality?.average_blur_score)}</dd>
          </dl>
          <div className="live-warnings">
            {(quality?.warnings ?? []).length ? (
              quality?.warnings.map((warning) => (
                <span key={warning}>
                  <CheckCircle2 size={13} />
                  {warning}
                </span>
              ))
            ) : (
              <span>
                <CheckCircle2 size={13} />
                {t("live.noWarnings")}
              </span>
            )}
          </div>
        </>
      ) : (
        <p className="empty">{t("live.empty")}</p>
      )}
    </div>
  );
}

function liveStatusLabel(status: string, t: Translator): string {
  if (status === "running") return t("live.statusRunning");
  if (status === "completed") return t("live.statusCompleted");
  if (status === "failed") return t("status.failed");
  return status;
}

function formatFixed(value: number | undefined) {
  return typeof value === "number" ? value.toFixed(2) : "-";
}
