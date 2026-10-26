import { describe, expect, it } from "vitest";
import { displayAssetPath } from "../lib/assetPath";

describe("displayAssetPath", () => {
  it("shows package-relative paths without a user's home directory", () => {
    expect(displayAssetPath("/Users/private/work/output/task/motrix_scene/meshes/object.obj"))
      .toBe("motrix_scene/meshes/object.obj");
  });
  it("normalizes Windows paths", () => {
    expect(displayAssetPath("C:\\Users\\private\\motrix_scene\\scene.xml"))
      .toBe("motrix_scene/scene.xml");
  });
  it("only shows a filename for files outside a scene package", () => {
    expect(displayAssetPath("/home/private/captures/motrix_scene.zip")).toBe("motrix_scene.zip");
    expect(displayAssetPath("/home/private/motrix_scene_backup/mesh.obj")).toBe("mesh.obj");
  });
  it("accepts relative and empty paths", () => {
    expect(displayAssetPath("motrix_scene/scene.xml")).toBe("motrix_scene/scene.xml");
    expect(displayAssetPath("")).toBe("");
  });
});
