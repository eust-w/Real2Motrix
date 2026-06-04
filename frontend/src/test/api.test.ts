import { describe, expect, it, vi } from "vitest";
import { api, resolveApiBase } from "../lib/api";

describe("api client", () => {
  it("surfaces backend error details", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: "Bad Request",
      json: async () => ({ detail: "missing COLMAP" })
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.listProjects()).rejects.toThrow("missing COLMAP");
  });

  it("builds project file URLs with encoded path segments", () => {
    expect(api.fileUrl("project 1", "motrix_scene/meshes/material 0.jpeg")).toBe(
      "http://localhost:8000/api/projects/project 1/files/motrix_scene/meshes/material%200.jpeg"
    );
  });

  it("defaults API base to the current browser host", () => {
    expect(resolveApiBase(undefined, { protocol: "http:", hostname: "127.0.0.1" })).toBe("http://127.0.0.1:8000");
  });

  it("builds file URLs from generated asset paths", () => {
    expect(
      api.assetFileUrl(
        "project-1",
        "/Users/longtaowu/workspace/Real2Motrix/backend/outputs/project-1/motrix_scene/meshes/objects/object_001/visual.obj"
      )
    ).toBe(
      "http://localhost:8000/api/projects/project-1/files/motrix_scene/meshes/objects/object_001/visual.obj"
    );
  });

  it("supports task update, delete, and regeneration requests", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: "task-1", name: "Edited task" })
    });
    vi.stubGlobal("fetch", fetchMock);

    await (api as any).updateProject("task-1", {
      name: "Edited task",
      description: "Updated",
      source_type: "mesh"
    });
    await (api as any).regenerateProject("task-1");
    await (api as any).deleteProject("task-1");

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "http://localhost:8000/api/projects/task-1",
      expect.objectContaining({ method: "PATCH" })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "http://localhost:8000/api/projects/task-1/regenerate",
      expect.objectContaining({ method: "POST" })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      "http://localhost:8000/api/projects/task-1",
      expect.objectContaining({ method: "DELETE" })
    );
  });
});
