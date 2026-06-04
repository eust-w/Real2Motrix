from pathlib import Path

from app.pipeline.reconstruction import colmap_runner


def test_select_best_sparse_model_prefers_largest_reconstruction(tmp_path: Path, monkeypatch) -> None:
    sparse_dir = tmp_path / "sparse"
    small = sparse_dir / "0"
    large = sparse_dir / "1"
    small.mkdir(parents=True)
    large.mkdir()

    def fake_stats(model_dir: Path) -> colmap_runner.SparseModelStats:
        if model_dir == small:
            return colmap_runner.SparseModelStats(path=model_dir, cameras=1, registered_images=3, points=2)
        return colmap_runner.SparseModelStats(path=model_dir, cameras=1, registered_images=38, points=4923)

    monkeypatch.setattr(colmap_runner, "_read_sparse_model_stats", fake_stats)

    assert colmap_runner._select_best_sparse_model(sparse_dir) == large


def test_colmap_openmvs_uses_video_oriented_quality_options(tmp_path: Path, monkeypatch) -> None:
    image_dir = tmp_path / "frames"
    image_dir.mkdir()
    (image_dir / "frame_000001.jpg").write_bytes(b"fake image")
    work_dir = tmp_path / "work"
    commands: list[list[str]] = []

    def fake_run_command(command, cwd, log=None, timeout=None) -> None:
        command_list = [str(item) for item in command]
        commands.append(command_list)
        if command_list[:2] == ["colmap", "mapper"]:
            (work_dir / "sparse" / "0").mkdir(parents=True)
        if command_list[:2] == ["colmap", "image_undistorter"]:
            (work_dir / "undistorted" / "sparse").mkdir(parents=True)
            (work_dir / "undistorted" / "sparse" / "cameras.bin").write_bytes(b"cameras")
        if command_list[0] == "InterfaceCOLMAP":
            (work_dir / "mvs" / "scene.mvs").write_bytes(b"scene")
        if command_list[0] == "DensifyPointCloud":
            (work_dir / "mvs" / "scene_dense.mvs").write_bytes(b"dense")
        if command_list[0] == "ReconstructMesh":
            (work_dir / "mvs" / "scene_dense_mesh.ply").write_bytes(b"mesh")
        if command_list[0] == "RefineMesh":
            (work_dir / "mvs" / "scene_dense_mesh_refine.ply").write_bytes(b"refined")
        if command_list[0] == "TextureMesh":
            (work_dir / "mvs" / "scene_dense_mesh_refine_texture.obj").write_bytes(b"obj")

    monkeypatch.setattr(colmap_runner, "require_dependencies", lambda dependencies: None)
    monkeypatch.setattr(colmap_runner, "run_command", fake_run_command)
    monkeypatch.setattr(colmap_runner, "_select_best_sparse_model", lambda sparse_dir, log=None: sparse_dir / "0")

    result = colmap_runner.reconstruct_images_with_colmap_openmvs(
        image_dir,
        work_dir,
        single_camera=True,
        match_strategy="sequential",
    )

    assert result == work_dir / "mvs" / "scene_dense_mesh_refine_texture.obj"
    feature_command = commands[0]
    assert feature_command[:2] == ["colmap", "feature_extractor"]
    assert feature_command[feature_command.index("--ImageReader.single_camera") + 1] == "1"
    assert feature_command[feature_command.index("--ImageReader.camera_model") + 1] == "SIMPLE_RADIAL"
    assert feature_command[feature_command.index("--SiftExtraction.max_num_features") + 1] == "16384"

    matcher_command = commands[1]
    assert matcher_command[:2] == ["colmap", "sequential_matcher"]
    assert matcher_command[matcher_command.index("--SequentialMatching.overlap") + 1] == "15"

    undistort_command = next(command for command in commands if command[:2] == ["colmap", "image_undistorter"])
    assert undistort_command[undistort_command.index("--max_image_size") + 1] == "1600"

    densify_command = next(command for command in commands if command[0] == "DensifyPointCloud")
    assert densify_command[densify_command.index("--resolution-level") + 1] == "0"
    assert densify_command[densify_command.index("--number-views") + 1] == "8"
