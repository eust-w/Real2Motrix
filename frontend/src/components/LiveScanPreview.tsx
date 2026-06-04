import { useEffect, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { OBJLoader } from "three/examples/jsm/loaders/OBJLoader.js";
import type { LiveScanCoverage } from "../lib/types";

export function LiveScanPreview({ coverage, previewObjUrl }: { coverage: LiveScanCoverage | null; previewObjUrl?: string }) {
  const [container, setContainer] = useState<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!container) return undefined;
    let frame = 0;
    const width = container.clientWidth || 520;
    const height = container.clientHeight || 280;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#f8fafc");
    scene.up.set(0, 0, 1);

    const camera = new THREE.PerspectiveCamera(48, width / height, 0.01, 200);
    camera.up.set(0, 0, 1);
    camera.position.set(2.8, -3.4, 2.6);

    const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height);
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.target.set(0, 0, 0);

    scene.add(new THREE.HemisphereLight("#ffffff", "#cbd5e1", 2.4));
    const gridSize = gridExtent(coverage);
    const grid = new THREE.GridHelper(gridSize, Math.max(4, Math.round(gridSize / 0.5)), "#94a3b8", "#e2e8f0");
    grid.rotation.x = Math.PI / 2;
    scene.add(grid);
    scene.add(new THREE.AxesHelper(Math.min(1.5, gridSize / 2)));

    drawCoverage(scene, coverage);
    void loadPreviewMesh(scene, previewObjUrl).finally(() => frameScene(scene, controls, camera));

    const resizeObserver = new ResizeObserver(() => {
      const nextWidth = container.clientWidth || 520;
      const nextHeight = container.clientHeight || 280;
      camera.aspect = nextWidth / nextHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(nextWidth, nextHeight);
    });
    resizeObserver.observe(container);

    function animate() {
      frame = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }
    animate();

    return () => {
      cancelAnimationFrame(frame);
      resizeObserver.disconnect();
      controls.dispose();
      disposeObject(scene);
      renderer.dispose();
      container.innerHTML = "";
    };
  }, [container, coverage, previewObjUrl]);

  return <div className="live-preview-canvas" ref={setContainer} />;
}

async function loadPreviewMesh(scene: THREE.Scene, previewObjUrl: string | undefined) {
  if (!previewObjUrl) return;
  try {
    const object = await new OBJLoader().loadAsync(previewObjUrl);
    object.name = "live_preview_mesh";
    object.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.material = new THREE.MeshStandardMaterial({
          color: "#64748b",
          roughness: 0.78,
          metalness: 0.02,
          transparent: true,
          opacity: 0.48,
          side: THREE.DoubleSide,
          wireframe: true
        });
      }
    });
    scene.add(object);
  } catch {
    // The coverage preview remains useful while the first mesh snapshot is still uploading.
  }
}

function drawCoverage(scene: THREE.Scene, coverage: LiveScanCoverage | null) {
  if (!coverage) return;
  const cellSize = coverage.cell_size_m || 0.5;
  const coveredMaterial = new THREE.MeshBasicMaterial({ color: "#0f766e", transparent: true, opacity: 0.68 });
  const weakMaterial = new THREE.MeshBasicMaterial({ color: "#ef4444", transparent: true, opacity: 0.3, wireframe: true });

  for (const cell of coverage.cells ?? []) {
    const tile = new THREE.Mesh(new THREE.BoxGeometry(cellSize * 0.92, cellSize * 0.92, 0.02), coveredMaterial.clone());
    tile.position.set(cell.x, cell.z, 0.01);
    scene.add(tile);
  }

  for (const cell of (coverage.weak_cells ?? []).slice(0, 64)) {
    const tile = new THREE.Mesh(new THREE.BoxGeometry(cellSize * 0.92, cellSize * 0.92, 0.026), weakMaterial.clone());
    tile.position.set(cell.x, cell.z, 0.035);
    scene.add(tile);
  }

  const pathPoints = (coverage.camera_path ?? []).map((point) => new THREE.Vector3(point.x, point.z, point.y + 0.12));
  if (pathPoints.length >= 2) {
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(pathPoints),
      new THREE.LineBasicMaterial({ color: "#2563eb", linewidth: 2 })
    );
    scene.add(line);
  }

  if (coverage.last_position) {
    const marker = new THREE.Mesh(
      new THREE.SphereGeometry(Math.max(0.055, cellSize * 0.14), 20, 12),
      new THREE.MeshStandardMaterial({ color: "#f59e0b", roughness: 0.45 })
    );
    marker.position.set(coverage.last_position.x, coverage.last_position.z, coverage.last_position.y + 0.18);
    scene.add(marker);
  }
}

function frameScene(scene: THREE.Scene, controls: Pick<OrbitControls, "target">, camera: THREE.PerspectiveCamera) {
  const box = new THREE.Box3().setFromObject(scene);
  if (box.isEmpty()) return;
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  const radius = Math.max(size.x, size.y, size.z, 1.5);
  controls.target.set(center.x, center.y, Math.max(0, center.z));
  camera.position.set(center.x + radius * 0.85, center.y - radius * 1.15, center.z + radius * 0.85);
  camera.lookAt(controls.target);
}

function gridExtent(coverage: LiveScanCoverage | null) {
  if (!coverage?.bounds) return 4;
  const width = Math.abs(coverage.bounds.max_x - coverage.bounds.min_x);
  const depth = Math.abs(coverage.bounds.max_z - coverage.bounds.min_z);
  return Math.max(4, Math.ceil(Math.max(width, depth) + 1));
}

function disposeObject(object: THREE.Object3D) {
  object.traverse((child) => {
    if (child instanceof THREE.Mesh || child instanceof THREE.Line) {
      child.geometry.dispose();
      const material = child.material;
      if (Array.isArray(material)) {
        material.forEach((item) => item.dispose());
      } else {
        material.dispose();
      }
    }
  });
}
