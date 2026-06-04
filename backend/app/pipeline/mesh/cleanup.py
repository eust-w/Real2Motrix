import numpy as np
import trimesh


def clean_visual_mesh(mesh: trimesh.Trimesh, *, prune_small_components: bool = True) -> trimesh.Trimesh:
    cleaned = mesh.copy()
    cleaned.remove_unreferenced_vertices()
    try:
        cleaned.update_faces(cleaned.nondegenerate_faces())
    except Exception:
        cleaned.remove_degenerate_faces()
    cleaned.remove_unreferenced_vertices()
    cleaned.merge_vertices()
    try:
        cleaned.fix_normals()
    except Exception:
        pass
    try:
        cleaned.fill_holes()
    except Exception:
        pass
    if prune_small_components:
        cleaned = _largest_components(cleaned)
    cleaned = _align_to_motrix_frame(cleaned)
    cleaned.metadata["unit"] = "meter"
    return cleaned


def _largest_components(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    try:
        parts = mesh.split(only_watertight=False)
    except ImportError:
        return mesh
    if len(parts) <= 1:
        return mesh
    areas = np.array([part.area for part in parts])
    max_area = float(areas.max())
    kept = [part for part, area in zip(parts, areas) if area >= max_area * 0.02]
    return trimesh.util.concatenate(kept)


def _align_to_motrix_frame(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    bounds = mesh.bounds
    center_xy = bounds.mean(axis=0)
    translation = np.array([-center_xy[0], -center_xy[1], -bounds[0][2]])
    mesh.apply_translation(translation)
    return mesh
