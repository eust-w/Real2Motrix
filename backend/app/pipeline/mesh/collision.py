import trimesh


def make_collision_mesh(visual_mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    try:
        collision = visual_mesh.convex_hull
    except Exception:
        collision = trimesh.creation.box(extents=visual_mesh.extents)
        collision.apply_translation(visual_mesh.bounds.mean(axis=0))
    if len(collision.faces) >= len(visual_mesh.faces):
        collision = trimesh.creation.box(extents=visual_mesh.extents)
        collision.apply_translation(visual_mesh.bounds.mean(axis=0))
    collision.remove_unreferenced_vertices()
    collision.metadata["unit"] = "meter"
    return collision

