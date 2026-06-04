import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { JobLogs } from "../components/JobLogs";
import { createTranslator } from "../lib/i18n";
import type { JobLog } from "../lib/types";

function buildLogs(count: number): JobLog[] {
  return Array.from({ length: count }, (_, index) => ({
    id: index + 1,
    job_id: "job-1",
    level: "info",
    message: `log line ${index + 1}`,
    created_at: "2026-06-04T10:00:00.000Z"
  }));
}

describe("JobLogs", () => {
  it("renders only the latest log window instead of expanding every log row", () => {
    const markup = renderToStaticMarkup(<JobLogs logs={buildLogs(120)} t={createTranslator("zh")} />);

    expect((markup.match(/class="log-row info"/g) ?? []).length).toBe(80);
    expect(markup).toContain("仅显示最近 80 条，共 120 条。");
    expect(markup).toContain("<span>log line 120</span>");
    expect(markup).not.toContain("<span>log line 1</span>");
  });
});
