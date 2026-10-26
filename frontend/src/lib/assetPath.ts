export function displayAssetPath(path: string): string {
  const parts = path.replace(/\\/g, "/").split("/").filter(Boolean);
  const packageIndex = parts.lastIndexOf("motrix_scene");
  return packageIndex >= 0 ? parts.slice(packageIndex).join("/") : parts[parts.length - 1] ?? "";
}
