#!/usr/bin/env bash
set -euo pipefail

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required for this helper. Install Homebrew first." >&2
  exit 1
fi

brew install ffmpeg colmap blender

cat <<'EOF'

Homebrew did not expose an OpenMVS formula on this machine.
Install OpenMVS from source or a trusted binary release, then ensure these executables are on PATH:
  InterfaceCOLMAP
  DensifyPointCloud
  ReconstructMesh
  RefineMesh
  TextureMesh

iOS build/run also requires full Xcode:
  sudo xcode-select -s /Applications/Xcode.app/Contents/Developer

After setup, run:
  python3 scripts/check_dependencies.py
EOF
