#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from typing import Dict


TOOLS = [
    "python3",
    "node",
    "npm",
    "ffmpeg",
    "colmap",
    "InterfaceCOLMAP",
    "DensifyPointCloud",
    "ReconstructMesh",
    "RefineMesh",
    "TextureMesh",
    "blender",
    "swift",
    "xcodebuild",
    "xcodegen",
]


def inspect(name: str) -> Dict:
    executable = shutil.which(name)
    version = None
    if executable:
        try:
            result = subprocess.run(
                [executable, "--version"],
                capture_output=True,
                text=True,
                timeout=6,
                check=False,
            )
            version = (result.stdout or result.stderr).splitlines()[0] if (result.stdout or result.stderr) else None
        except Exception as exc:
            version = f"version check failed: {exc}"
    return {"available": executable is not None, "executable": executable, "version": version}


def main() -> int:
    report = {tool: inspect(tool) for tool in TOOLS}
    print(json.dumps(report, indent=2))
    missing = [tool for tool, item in report.items() if not item["available"]]
    if missing:
        print("\nMissing tools: " + ", ".join(missing), file=sys.stderr)
        print("Real2Motrix will fail jobs that require missing tools instead of fabricating results.", file=sys.stderr)
        return 1
    xcode = subprocess.run(["xcode-select", "-p"], capture_output=True, text=True, check=False)
    if "CommandLineTools" in xcode.stdout:
        print("\nFull Xcode is not selected; iOS app build/run requires Xcode, not CommandLineTools.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
