import { useEffect, useState } from "react";
import * as THREE from "three";
import { MTLLoader } from "three/examples/jsm/loaders/MTLLoader.js";
import { OBJLoader } from "three/examples/jsm/loaders/OBJLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { Maximize2, Minimize2 } from "lucide-react";
import type { Locale, Translator } from "../lib/i18n";

export type PreviewMode = "scene" | "visual" | "collision";

export type PreviewStats = {
  visual_faces?: number;
  collision_faces?: number;
  bbox?: number[][];
  object_count?: number;
};

export type PreviewObjectAsset = {
  id: string;
  label: string;
  visualUrl: string;
  collisionUrl?: string;
};

type SceneIndex = {
  name?: string;
  type?: string;
  entry?: string;
  entries?: { mjcf?: string; urdf?: string };
  assets?: Record<string, string>;
};

type AssetManifest = {
  unit?: string;
  coordinate_system?: string;
  visual_faces?: number;
  collision_faces?: number;
  bbox?: number[][];
  scene?: PreviewStats;
  objects?: Array<PreviewStats & { id?: string }>;
  segmentation?: { object_count?: number };
};

type MeshPreviewProps = {
  visualUrl: string;
  collisionUrl: string;
  sceneUrl: string;
  manifestUrl: string;
  materialUrl: string;
  materialBaseUrl: string;
  mode: PreviewMode;
  selectedLabel?: string;
  selectedStats?: PreviewStats | null;
  objectAssets?: PreviewObjectAsset[];
  locale: Locale;
  t: Translator;
  onModeChange: (mode: PreviewMode) => void;
};

export function MeshPreview({
  visualUrl,
  collisionUrl,
  sceneUrl,
  manifestUrl,
  materialUrl,
  materialBaseUrl,
  mode,
  selectedLabel,
  selectedStats,
  objectAssets = [],
  locale,
  t,
  onModeChange
}: MeshPreviewProps) {
  const [container, setContainer] = useState<HTMLDivElement | null>(null);
  const [message, setMessage] = useState(t("preview.unavailable"));
  const [sceneIndex, setSceneIndex] = useState<SceneIndex | null>(null);
  const [manifest, setManifest] = useState<AssetManifest | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    let disposed = false;
    async function loadMetadata() {
      const [sceneResponse, manifestResponse] = await Promise.allSettled([
        fetch(sceneUrl).then((response) => (response.ok ? response.json() : null)),
        fetch(manifestUrl).then((response) => (response.ok ? response.json() : null))
      ]);
      if (disposed) return;
      setSceneIndex(sceneResponse.status === "fulfilled" ? sceneResponse.value : null);
      setManifest(manifestResponse.status === "fulfilled" ? manifestResponse.value : null);
    }
    void loadMetadata();
    return () => {
      disposed = true;
    };
  }, [sceneUrl, manifestUrl]);

  useEffect(() => {
    if (!isFullscreen) return undefined;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsFullscreen(false);
      }
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [isFullscreen]);

  useEffect(() => {
    if (!container) return undefined;
    let disposed = false;
    let frame = 0;
    setMessage(mode === "scene" ? t("preview.loadingScene") : t("preview.loadingAsset"));

    const width = container.clientWidth || 720;
    const height = container.clientHeight || 430;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#f8fafc");
    scene.up.set(0, 0, 1);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.01, 1000);
    camera.up.set(0, 0, 1);
    camera.position.set(2.6, -3.2, 2.15);

    const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height);
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.target.set(0, 0, 0.75);

    scene.add(new THREE.HemisphereLight("#ffffff", "#94a3b8", 2.2));
    const keyLight = new THREE.DirectionalLight("#ffffff", 2.4);
    keyLight.position.set(4, -5, 7);
    scene.add(keyLight);

    const grid = new THREE.GridHelper(5, 10, "#94a3b8", "#e2e8f0");
    grid.rotation.x = Math.PI / 2;
    scene.add(grid);
    scene.add(new THREE.AxesHelper(1.25));

    const resizeObserver = new ResizeObserver(() => {
      const nextWidth = container.clientWidth || 720;
      const nextHeight = container.clientHeight || 430;
      camera.aspect = nextWidth / nextHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(nextWidth, nextHeight);
    });
    resizeObserver.observe(container);

    async function loadVisualObject(url = visualUrl, color = "#0f766e", usePackageMaterial = true) {
      const loader = new OBJLoader();
      if (usePackageMaterial) {
        try {
          const materialLoader = new MTLLoader();
          materialLoader.setCrossOrigin("anonymous");
          materialLoader.setResourcePath(materialBaseUrl);
          const materials = await materialLoader.loadAsync(materialUrl);
          materials.preload();
          loader.setMaterials(materials);
        } catch {
          // The package still previews if material assets are not present yet.
        }
      }
      const visual = await loader.loadAsync(url);
      visual.name = "visual_mesh";
      visual.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          if (!child.material || (Array.isArray(child.material) && child.material.length === 0)) {
            child.material = new THREE.MeshStandardMaterial({ color, roughness: 0.74, metalness: 0.04 });
          }
          applyMaterialSide(child.material);
        }
      });
      return visual;
    }

    async function loadCollisionObject(url: string, sceneOverlay: boolean) {
      const collision = await new OBJLoader().loadAsync(url);
      collision.name = "collision_mesh";
      collision.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          child.material = new THREE.MeshBasicMaterial({
            color: "#f59e0b",
            wireframe: true,
            transparent: sceneOverlay,
            opacity: sceneOverlay ? 0.58 : 1,
            depthWrite: !sceneOverlay
          });
        }
      });
      return collision;
    }

    async function loadPreview() {
      try {
        const group = new THREE.Group();
        if (mode === "scene") {
          group.add(await loadVisualObject());
          group.add(await loadCollisionObject(collisionUrl, true));
          for (const [index, asset] of objectAssets.entries()) {
            try {
              const color = objectColor(index);
              const objectGroup = new THREE.Group();
              objectGroup.name = asset.id;
              objectGroup.add(await loadVisualObject(asset.visualUrl, color, false));
              if (asset.collisionUrl) {
                objectGroup.add(await loadCollisionObject(asset.collisionUrl, true));
              }
              group.add(objectGroup);
            } catch {
              // Keep the main scene visible even if one generated object asset is missing.
            }
          }
        } else if (mode === "visual") {
          group.add(await loadVisualObject());
        } else {
          group.add(await loadCollisionObject(collisionUrl, false));
        }
        if (disposed) return;
        frameObjectForPreview(group, scene, controls);
        scene.add(group);
        setMessage("");
      } catch {
        if (!disposed) setMessage(t("preview.unavailable"));
      }
    }

    function animate() {
      frame = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }

    void loadPreview();
    animate();

    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      resizeObserver.disconnect();
      controls.dispose();
      disposeObject(scene);
      renderer.dispose();
      container.innerHTML = "";
    };
  }, [container, visualUrl, collisionUrl, materialUrl, materialBaseUrl, mode, objectAssets, t]);

  const manifestStats = manifest?.scene ?? manifest;
  const displayStats = selectedStats ?? manifestStats;
  const objectCount = selectedStats?.object_count ?? manifest?.segmentation?.object_count ?? manifest?.objects?.length ?? 0;

  return (
    <div className={isFullscreen ? "mesh-preview-wrap fullscreen" : "mesh-preview-wrap"}>
      <div className="mesh-toolbar" role="tablist" aria-label={t("preview.subtitle")}>
        <button className={mode === "scene" ? "selected" : ""} onClick={() => onModeChange("scene")}>
          {t("preview.motrixScene")}
        </button>
        <button className={mode === "visual" ? "selected" : ""} onClick={() => onModeChange("visual")}>
          {t("preview.visualAsset")}
        </button>
        <button className={mode === "collision" ? "selected" : ""} onClick={() => onModeChange("collision")}>
          {t("preview.collisionAsset")}
        </button>
        <button
          className="fullscreen-toggle"
          type="button"
          aria-pressed={isFullscreen}
          aria-label={isFullscreen ? t("preview.exitFullscreen") : t("preview.enterFullscreen")}
          onClick={() => setIsFullscreen((current) => !current)}
        >
          {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          {isFullscreen ? t("preview.exitFullscreen") : t("preview.enterFullscreen")}
        </button>
      </div>
      <div className="scene-meta">
        <span>{selectedLabel ?? t("preview.completeScene")}</span>
        <span>{sceneIndex?.entry ?? "scene.xml"}</span>
        <span>{sceneIndex?.entries?.urdf ?? "scene.urdf"}</span>
        <span>{manifest?.coordinate_system ?? "motrix_world"}</span>
        <span>{manifest?.unit ?? "meter"}</span>
        <span>{t("preview.objects", { count: objectCount })}</span>
      </div>
      <div className="mesh-preview" ref={setContainer} />
      <div className="asset-stats" aria-label={t("preview.title")}>
        <span>{t("stats.visualFaces", { value: formatNumber(displayStats?.visual_faces, locale) })}</span>
        <span>{t("stats.collisionFaces", { value: formatNumber(displayStats?.collision_faces, locale) })}</span>
        <span>{t("stats.bbox", { value: formatBounds(displayStats?.bbox) })}</span>
      </div>
      {message ? <div className="preview-message">{message}</div> : null}
    </div>
  );
}

function objectColor(index: number) {
  const colors = ["#2563eb", "#c2410c", "#7c3aed", "#0f766e", "#be123c", "#047857"];
  return colors[index % colors.length];
}

export function frameObjectForPreview(
  group: THREE.Group,
  scene: THREE.Scene,
  controls: Pick<OrbitControls, "target">
) {
  const box = new THREE.Box3().setFromObject(group);
  if (box.isEmpty()) return;
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const maxAxis = Math.max(size.x, size.y, size.z);
  const scale = maxAxis > 0 ? 2.25 / maxAxis : 1;
  group.scale.setScalar(scale);
  group.position.set(-center.x * scale, -center.y * scale, -box.min.z * scale);
  controls.target.set(0, 0, (size.z * scale) / 2);
  scene.updateMatrixWorld();
}

function applyMaterialSide(material: THREE.Material | THREE.Material[]) {
  const materials = Array.isArray(material) ? material : [material];
  materials.forEach((item) => {
    item.side = THREE.DoubleSide;
    item.needsUpdate = true;
  });
}

function disposeObject(object: THREE.Object3D) {
  object.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      child.geometry.dispose();
      const materials = Array.isArray(child.material) ? child.material : [child.material];
      materials.forEach((material) => material.dispose());
    }
  });
}

function formatNumber(value: number | undefined, locale: Locale) {
  return typeof value === "number" ? value.toLocaleString(locale === "zh" ? "zh-CN" : "en-US") : "-";
}

function formatBounds(bounds: number[][] | undefined) {
  if (!bounds || bounds.length < 2) return "-";
  const size = bounds[1].map((value, index) => Math.abs(value - (bounds[0][index] ?? 0)));
  return size.map((value) => value.toFixed(2)).join(" x ");
}
