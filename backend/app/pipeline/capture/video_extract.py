from pathlib import Path
from typing import Callable, Optional

from app.pipeline.utils.dependencies import require_dependencies
from app.pipeline.utils.subprocess_utils import run_command


def extract_video_frames(
    video_path: Path,
    output_dir: Path,
    log: Optional[Callable[[str, str], None]] = None,
    fps: int = 6,
) -> Path:
    require_dependencies(["ffmpeg"])
    video_path = Path(video_path).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    frame_pattern = (output_dir / "frame_%06d.jpg").resolve()
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-vf",
            f"fps={fps}",
            frame_pattern,
        ],
        cwd=output_dir,
        log=log,
    )
    if not any(output_dir.glob("*.jpg")):
        raise RuntimeError("ffmpeg completed but no frames were extracted")
    return output_dir
