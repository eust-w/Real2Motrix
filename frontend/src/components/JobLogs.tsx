import type { Translator } from "../lib/i18n";
import type { JobLog } from "../lib/types";

export const LOG_RENDER_LIMIT = 80;

export function JobLogs({ logs, t }: { logs: JobLog[]; t: Translator }) {
  const visibleLogs = logs.slice(-LOG_RENDER_LIMIT);

  return (
    <div className="panel logs-panel">
      <div className="panel-header">
        <div>
          <p>{t("logs.subtitle")}</p>
          <h2>{t("logs.title")}</h2>
        </div>
      </div>
      {logs.length > visibleLogs.length ? (
        <p className="log-window-note">{t("logs.visibleWindow", { shown: visibleLogs.length, total: logs.length })}</p>
      ) : null}
      <div className="logs">
        {logs.length === 0 ? (
          <span className="empty">{t("logs.empty")}</span>
        ) : (
          visibleLogs.map((log) => (
            <div className={`log-row ${log.level}`} key={log.id}>
              <time>{new Date(log.created_at).toLocaleTimeString()}</time>
              <strong>{log.level}</strong>
              <span>{log.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
