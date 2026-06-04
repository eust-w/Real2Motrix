from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import trimesh

from app.pipeline.mesh.collision import make_collision_mesh


@dataclass
class ObjectAsset:
    object_id: str
    visual: trimesh.Trimesh
    collision: trimesh.Trimesh
    manifest: Dict[str, Any]


@dataclass
class SceneObjectAssets:
    scene_visual: trimesh.Trimesh
    scene_collision: trimesh.Trimesh
    objects: List[ObjectAsset]
    segmentation: Dict[str, Any]


def split_scene_objects(
    visual_mesh: trimesh.Trimesh,
    *,
    max_objects: int = 16,
    min_area_ratio: float = 0.005,
    min_extent_ratio: float = 0.01,
) -> SceneObjectAssets:
    parts = _split_components(visual_mesh)
    total_area = float(max(visual_mesh.area, 0.0))
    total_faces = int(len(visual_mesh.faces))
    scene_extent = float(max(visual_mesh.extents)) if len(visual_mesh.extents) else 0.0
    min_faces = max(24, int(total_faces * 0.001))
    min_area = max(total_area * min_area_ratio, 1e-8)
    min_extent = max(scene_extent * min_extent_ratio, 1e-5)
    filters = _filters(min_faces, min_area, min_extent, max_objects)

    if len(parts) <= 1:
        clustered = _split_from_face_clusters(
            visual_mesh,
            min_faces=min_faces,
            min_area=min_area,
            min_extent=min_extent,
            max_objects=max_objects,
            filters=filters,
        )
        if clustered is not None:
            return clustered
        return _scene_only(visual_mesh, method="connected_components", component_count=len(parts), filters=filters)

    ranked = sorted(
        enumerate(parts),
        key=lambda item: (float(item[1].area), int(len(item[1].faces))),
        reverse=True,
    )
    environment_index = ranked[0][0]
    object_indices: List[int] = []
    rejected: List[Dict[str, Any]] = []

    for component_index, part in ranked:
        stats = _component_stats(part)
        if component_index == environment_index:
            rejected.append({**stats, "component_index": component_index, "reason": "largest_component_as_scene"})
            continue
        reason = _reject_reason(part, min_faces=min_faces, min_area=min_area, min_extent=min_extent)
        if reason:
            rejected.append({**stats, "component_index": component_index, "reason": reason})
            continue
        object_indices.append(component_index)
        if len(object_indices) >= max_objects:
            break

    object_index_set = set(object_indices)
    scene_parts = [part.copy() for index, part in enumerate(parts) if index not in object_index_set]
    scene_visual = trimesh.util.concatenate(scene_parts) if scene_parts else visual_mesh.copy()
    objects: List[ObjectAsset] = []
    for ordinal, component_index in enumerate(object_indices, start=1):
        visual = parts[component_index].copy()
        objects.append(
            _make_object_asset(ordinal, visual, "connected_component", {"component_index": int(component_index)})
        )

    segmentation = {
        "method": "connected_components",
        "component_count": len(parts),
        "object_count": len(objects),
        "environment_component_index": environment_index,
        "filters": filters,
        "rejected_components": rejected,
    }
    scene_collision = make_collision_mesh(scene_visual)
    return SceneObjectAssets(scene_visual=scene_visual, scene_collision=scene_collision, objects=objects, segmentation=segmentation)


def _scene_only(
    visual_mesh: trimesh.Trimesh,
    *,
    method: str,
    component_count: int,
    filters: Dict[str, Any],
) -> SceneObjectAssets:
    scene_visual = visual_mesh.copy()
    return SceneObjectAssets(
        scene_visual=scene_visual,
        scene_collision=make_collision_mesh(scene_visual),
        objects=[],
        segmentation={
            "method": method,
            "component_count": component_count,
            "object_count": 0,
            "filters": filters,
            "rejected_components": [],
        },
    )


def _split_from_face_clusters(
    visual_mesh: trimesh.Trimesh,
    *,
    min_faces: int,
    min_area: float,
    min_extent: float,
    max_objects: int,
    filters: Dict[str, Any],
) -> Optional[SceneObjectAssets]:
    try:
        from sklearn.cluster import DBSCAN
    except ImportError:
        return None

    face_count = int(len(visual_mesh.faces))
    if face_count < max(min_faces * 4, 1000):
        return None
    extents = visual_mesh.extents
    scale = np.where(extents <= 1e-9, 1.0, extents)
    features = (visual_mesh.triangles_center - visual_mesh.bounds[0]) / scale
    eps = 0.025
    min_samples = max(40, min(150, int(face_count * 0.0007)))
    labels = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=-1).fit_predict(features)
    clusters: List[Tuple[int, np.ndarray]] = []
    for label in sorted(set(int(item) for item in labels.tolist())):
        if label == -1:
            continue
        face_indices = np.flatnonzero(labels == label)
        if len(face_indices) > 0:
            clusters.append((int(label), face_indices))
    if len(clusters) <= 1:
        return None

    ranked = sorted(clusters, key=lambda item: int(len(item[1])), reverse=True)
    environment_label = ranked[0][0]
    selected: List[Tuple[int, np.ndarray, trimesh.Trimesh]] = []
    rejected: List[Dict[str, Any]] = []
    for label, face_indices in ranked:
        part = _submesh_by_faces(visual_mesh, face_indices)
        stats = {**_component_stats(part), "cluster_label": int(label), "cluster_faces": int(len(face_indices))}
        if label == environment_label:
            rejected.append({**stats, "reason": "largest_cluster_as_scene"})
            continue
        reason = _reject_reason(part, min_faces=min_faces, min_area=min_area, min_extent=min_extent)
        if reason:
            rejected.append({**stats, "reason": reason})
            continue
        selected.append((label, face_indices, part))
        if len(selected) >= max_objects:
            break

    if not selected:
        return None

    scene_face_mask = np.ones(face_count, dtype=bool)
    for _, face_indices, _ in selected:
        scene_face_mask[face_indices] = False
    scene_faces = np.flatnonzero(scene_face_mask)
    scene_visual = _submesh_by_faces(visual_mesh, scene_faces) if len(scene_faces) else visual_mesh.copy()
    objects = [
        _make_object_asset(
            ordinal,
            part,
            "dbscan_face_center_cluster",
            {"cluster_label": int(label), "cluster_faces": int(len(face_indices))},
        )
        for ordinal, (label, face_indices, part) in enumerate(selected, start=1)
    ]
    return SceneObjectAssets(
        scene_visual=scene_visual,
        scene_collision=make_collision_mesh(scene_visual),
        objects=objects,
        segmentation={
            "method": "connected_components+dbscan_face_centers",
            "component_count": 1,
            "object_count": len(objects),
            "cluster_count": len(clusters),
            "environment_cluster_label": int(environment_label),
            "noise_faces": int((labels == -1).sum()),
            "dbscan": {"eps": eps, "min_samples": int(min_samples), "feature_space": "normalized_face_centers"},
            "filters": filters,
            "rejected_components": rejected,
        },
    )


def _split_components(mesh: trimesh.Trimesh) -> List[trimesh.Trimesh]:
    try:
        parts = list(mesh.split(only_watertight=False))
    except ImportError:
        return [mesh.copy()]
    if not parts:
        return [mesh.copy()]
    return [part.copy() for part in parts if len(part.faces) > 0 and len(part.vertices) > 0]


def _reject_reason(mesh: trimesh.Trimesh, *, min_faces: int, min_area: float, min_extent: float) -> Optional[str]:
    if int(len(mesh.faces)) < min_faces:
        return "below_min_faces"
    if float(mesh.area) < min_area:
        return "below_min_area"
    if float(max(mesh.extents)) < min_extent:
        return "below_min_extent"
    if not np.isfinite(mesh.bounds).all():
        return "non_finite_bounds"
    return None


def _make_object_asset(
    ordinal: int,
    visual: trimesh.Trimesh,
    source: str,
    extra: Dict[str, Any],
) -> ObjectAsset:
    collision = make_collision_mesh(visual)
    object_id = f"object_{ordinal:03d}"
    binding_type = "static_world_geometry_cluster" if source == "dbscan_face_center_cluster" else "static_world_mesh_component"
    return ObjectAsset(
        object_id=object_id,
        visual=visual,
        collision=collision,
        manifest={
            "id": object_id,
            "role": "object_candidate",
            "source": source,
            **extra,
            "visual_mesh": f"meshes/objects/{object_id}/visual.obj",
            "collision_mesh": f"meshes/objects/{object_id}/collision.obj",
            "visual_faces": int(len(visual.faces)),
            "collision_faces": int(len(collision.faces)),
            "bbox": _bounds(visual),
            "center": visual.bounds.mean(axis=0).tolist(),
            "extents": visual.extents.tolist(),
            "surface_area": float(visual.area),
            "binding": {
                "type": binding_type,
                "body": object_id,
                "pose_source": "mesh_vertices_in_world_frame",
            },
            "gaussian_splat": None,
        },
    )


def _component_stats(mesh: trimesh.Trimesh) -> Dict[str, Any]:
    return {
        "visual_faces": int(len(mesh.faces)),
        "bbox": _bounds(mesh),
        "extents": mesh.extents.tolist(),
        "surface_area": float(mesh.area),
    }


def _bounds(mesh: trimesh.Trimesh) -> List[List[float]]:
    return mesh.bounds.tolist()


def _submesh_by_faces(mesh: trimesh.Trimesh, face_indices: np.ndarray) -> trimesh.Trimesh:
    submesh = mesh.submesh([np.asarray(face_indices, dtype=np.int64)], append=True, repair=False)
    submesh.remove_unreferenced_vertices()
    return submesh


def _filters(min_faces: int, min_area: float, min_extent: float, max_objects: int) -> Dict[str, Any]:
    return {
        "min_faces": int(min_faces),
        "min_area": float(min_area),
        "min_extent": float(min_extent),
        "max_objects": int(max_objects),
    }
