import { ShieldCheck } from "lucide-react";
import type { Translator } from "../lib/i18n";

export function ValidationReport({
  validation,
  onValidate,
  t
}: {
  validation: Record<string, unknown> | null;
  onValidate: () => void;
  t: Translator;
}) {
  const valid = validation?.valid as boolean | undefined;
  const issues = (validation?.issues as Array<{ level: string; message: string }> | undefined) ?? [];
  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <p>{t("validation.subtitle")}</p>
          <h2>{t("validation.title")}</h2>
        </div>
        <button className="ghost compact" onClick={onValidate}>
          <ShieldCheck size={15} />
          {t("actions.validate")}
        </button>
      </div>
      {validation ? (
        <>
          <div className={`status-pill ${valid ? "completed" : "failed"}`}>
            {valid ? t("validation.valid") : t("validation.invalid")}
          </div>
          <div className="issue-list">
            {issues.length === 0 ? (
              <span className="empty">{t("validation.noIssues")}</span>
            ) : (
              issues.map((issue, index) => (
                <div className="issue-row" key={`${issue.message}-${index}`}>
                  <strong>{issue.level}</strong>
                  <span>{issue.message}</span>
                </div>
              ))
            )}
          </div>
        </>
      ) : (
        <p className="empty">{t("validation.empty")}</p>
      )}
    </div>
  );
}
