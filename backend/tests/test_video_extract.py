from pathlib import Path

from app.pipeline.capture import video_extract


def test_extract_video_frames_resolves_relative_input_before_changing_cwd(tmp_path: Path, monkeypatch) -> None:
    video_path = tmp_path / "input.mp4"
    video_path.write_bytes(b"fake")
    commands = []

    def fake_run_command(command, cwd, log=None, timeout=None):
        commands.append((command, cwd))
        (cwd / "frame_000001.jpg").write_bytes(b"jpg")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(video_extract, "require_dependencies", lambda dependencies: None)
    monkeypatch.setattr(video_extract, "run_command", fake_run_command)

    video_extract.extract_video_frames(Path("input.mp4"), tmp_path / "frames")

    command, cwd = commands[0]
    input_arg = command[command.index("-i") + 1]
    frame_pattern = command[-1]
    assert Path(input_arg).is_absolute()
    assert Path(frame_pattern).is_absolute()
    assert cwd == tmp_path / "frames"
