import subprocess
from pathlib import Path
from typing import Callable, Iterable, Optional


def run_command(
    command: Iterable[str],
    cwd: Path,
    log: Optional[Callable[[str, str], None]] = None,
    timeout: Optional[int] = None,
) -> None:
    command_list = [str(item) for item in command]
    if log:
        log("info", "$ " + " ".join(command_list))
    process = subprocess.Popen(
        command_list,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        assert process.stdout is not None
        for line in process.stdout:
            if log:
                log("info", line.rstrip())
        code = process.wait(timeout=timeout)
    except Exception:
        process.kill()
        raise
    if code != 0:
        raise RuntimeError(f"command failed with exit code {code}: {' '.join(command_list)}")

