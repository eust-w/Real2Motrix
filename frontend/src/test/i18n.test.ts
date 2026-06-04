import { describe, expect, it } from "vitest";
import { defaultLocale, isLocale, nextLocale, translate } from "../lib/i18n";

describe("i18n", () => {
  it("defaults to Chinese", () => {
    expect(defaultLocale).toBe("zh");
    expect(translate(defaultLocale, "actions.refresh")).toBe("刷新");
  });

  it("translates shared UI labels in Chinese and English", () => {
    expect(translate("zh", "preview.title")).toBe("Motrix 场景 / 3D 资产");
    expect(translate("en", "preview.title")).toBe("Motrix scene / 3D assets");
  });

  it("uses task language instead of project language", () => {
    expect(translate("zh", "newProject.title")).toBe("新任务");
    expect(translate("zh", "projects.title")).toBe("任务");
    expect(translate("zh", "workspace.noProject")).toBe("未选择任务");
    expect(translate("en", "newProject.title")).toBe("New task");
    expect(translate("en", "projects.title")).toBe("Tasks");
    expect(translate("en", "workspace.noProject")).toBe("No task selected");
  });

  it("recognizes supported locales and toggles between them", () => {
    expect(isLocale("zh")).toBe(true);
    expect(isLocale("en")).toBe(true);
    expect(isLocale("fr")).toBe(false);
    expect(nextLocale("zh")).toBe("en");
    expect(nextLocale("en")).toBe("zh");
  });
});
