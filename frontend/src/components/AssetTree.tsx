import { Eye, FileArchive, FileText } from "lucide-react";
import type { Translator } from "../lib/i18n";
import type { Asset } from "../lib/types";
import type { PreviewMode } from "./MeshPreview";
import { displayAssetPath } from "../lib/assetPath";

export function AssetTree({
  assets,
  activeMode,
  activeAssetId,
  t,
  onPreview
}: {
  assets: Asset[];
  activeMode: PreviewMode;
  activeAssetId: string | null;
  t: Translator;
  onPreview: (asset: Asset, mode: PreviewMode) => void;
}) {
  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <p>{t("assets.subtitle")}</p>
          <h2>{t("assets.title")}</h2>
        </div>
        <FileArchive size={20} />
      </div>
      <div className="asset-list">
        {assets.length === 0 ? (
          <p className="empty">{t("assets.empty")}</p>
        ) : (
          assets.map((asset) => {
            const previewMode = modeForAsset(asset.asset_type);
            const selected =
              activeAssetId === asset.id ||
              (!activeAssetId && asset.asset_type === "motrix_package" && activeMode === previewMode);
            return (
              <div className="asset-row" key={asset.id}>
                <FileText size={16} />
                <div>
                  <strong>{assetLabel(asset, t)}</strong>
                  <span>{displayAssetPath(asset.path)}</span>
                </div>
                {previewMode ? (
                  <button
                    className={selected ? "asset-preview-button selected" : "asset-preview-button"}
                    onClick={() => onPreview(asset, previewMode)}
                  >
                    <Eye size={14} />
                    {t("actions.preview")}
                  </button>
                ) : null}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

function modeForAsset(assetType: string): PreviewMode | null {
  if (assetType === "visual_mesh" || assetType === "scene_visual_mesh" || assetType === "object_visual_mesh") {
    return "visual";
  }
  if (assetType === "collision_mesh" || assetType === "scene_collision_mesh" || assetType === "object_collision_mesh") {
    return "collision";
  }
  if (assetType === "motrix_package") return "scene";
  return null;
}

function assetLabel(asset: Asset, t: Translator): string {
  const objectId = stringMeta(asset, "object_id") ?? stringMeta(asset, "id");
  if (objectId && asset.asset_type.startsWith("object_")) {
    return `${objectId} ${assetTypeLabel(asset.asset_type, t)}`;
  }
  return assetTypeLabel(asset.asset_type, t);
}

function stringMeta(asset: Asset, key: string): string | null {
  const value = asset.metadata_json[key];
  return typeof value === "string" ? value : null;
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
