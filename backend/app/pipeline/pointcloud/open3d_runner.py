from pathlib import Path


def pointcloud_to_mesh(source_path: Path, output_path: Path) -> Path:
    try:
        import open3d as o3d
    except ImportError as exc:
        raise RuntimeError(
            "Open3D is required for point cloud inputs. Install it in the backend environment before running PLY/PCD point cloud jobs."
        ) from exc

    cloud = o3d.io.read_point_cloud(str(source_path))
    if cloud.is_empty():
        raise ValueError(f"point cloud is empty: {source_path}")
    cloud.estimate_normals()
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(cloud, depth=8)
    if mesh.is_empty():
        raise RuntimeError("Open3D Poisson reconstruction produced an empty mesh")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    o3d.io.write_triangle_mesh(str(output_path), mesh)
    return output_path
