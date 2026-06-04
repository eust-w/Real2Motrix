import { Activity } from "lucide-react";
import type { Translator } from "../lib/i18n";
import type { Job } from "../lib/types";

export function JobProgress({
  job,
  t,
  formatStatus,
  formatSource
}: {
  job: Job | null;
  t: Translator;
  formatStatus: (status: string) => string;
  formatSource: (source: string) => string;
}) {
  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <p>{t("task.subtitle")}</p>
          <h2>{t("task.title")}</h2>
        </div>
        <Activity size={20} />
      </div>
      {job ? (
        <>
          <div className={`status-pill ${job.status}`}>{formatStatus(job.status)}</div>
          <div className="progress-track">
            <div style={{ width: `${job.progress}%` }} />
          </div>
          <dl className="details">
            <dt>{t("task.step")}</dt>
            <dd>{formatStatus(job.current_step)}</dd>
            <dt>{t("task.source")}</dt>
            <dd>{formatSource(job.source_type)}</dd>
            {job.error_message ? (
              <>
                <dt>{t("task.error")}</dt>
                <dd>{job.error_message}</dd>
              </>
            ) : null}
          </dl>
        </>
      ) : (
        <p className="empty">{t("task.empty")}</p>
      )}
    </div>
  );
}
