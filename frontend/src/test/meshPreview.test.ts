import { describe, expect, it } from "vitest";
import * as THREE from "three";
import * as MeshPreviewModule from "../components/MeshPreview";

describe("MeshPreview framing", () => {
  it("places the scaled object on the z=0 grid and centers it around the origin", () => {
    const frameObjectForPreview = (MeshPreviewModule as any).frameObjectForPreview;
    expect(frameObjectForPreview).toBeTypeOf("function");

    const group = new THREE.Group();
    const geometry = new THREE.BoxGeometry(2, 4, 6);
    geometry.translate(10, -3, 8);
    group.add(new THREE.Mesh(geometry));

    const scene = new THREE.Scene();
    const controls = { target: new THREE.Vector3() };

    frameObjectForPreview(group, scene, controls);
    scene.add(group);
    scene.updateMatrixWorld(true);

    const framedBox = new THREE.Box3().setFromObject(group);
    const framedCenter = framedBox.getCenter(new THREE.Vector3());

    expect(framedBox.min.z).toBeCloseTo(0, 5);
    expect(framedCenter.x).toBeCloseTo(0, 5);
    expect(framedCenter.y).toBeCloseTo(0, 5);
    expect(controls.target.z).toBeCloseTo(framedBox.getSize(new THREE.Vector3()).z / 2, 5);
  });
});
