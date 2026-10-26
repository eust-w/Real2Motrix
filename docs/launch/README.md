# Real2Motrix Alpha launch

Positioning: an open-source local capture and asset-processing workbench for
robotics simulation. The initial audience is reconstruction and robotics
developers, not consumers expecting a production phone scanner.

## Demonstration provenance

The video shows the real React/Three.js frontend and an actual HTTP API/worker
mesh job. Its input is original geometry produced by `scripts/launch_demo.py`.
It is **not a phone scan, video reconstruction, 3DGS result or physics benchmark**.
No private recordings, external models, music or signing material are included.
Chinese narration is synthesized with macOS `say` (Tingting).

## Published links

Verified on 2026-10-26:

- [GitHub Alpha release](https://github.com/eust-w/Real2Motrix/releases/tag/v0.1.0-alpha.1):
  original demo package, horizontal and vertical 1080p videos, and Chinese subtitles.
- [Gitea Alpha release](https://gitea.d-robotics.cc/longtao.wu/Real2Motrix/releases/tag/v0.1.0-alpha.1):
  source/tag mirror and links to the downloadable GitHub assets.
- [YouTube introduction](https://youtu.be/82gHy-zrwwU): published with public visibility.
- [X announcement with video](https://x.com/eustancewu/status/2114658476182139156):
  published with an AI-content disclosure.
- [Douyin introduction](https://www.douyin.com/video/7700918154871983395):
  review passed; public playback and AI-content disclosure verified.

Both source releases target `d13e06907b5c25144656c58262e4d0dc9f7b5726`.
[Core CI passed](https://github.com/eust-w/Real2Motrix/actions/runs/40302206805).
Other platform submissions are not claimed as public until independently verified.

## Local artifacts

The local launch directory is ignored by Git:

| File | Purpose |
| --- | --- |
| `Real2Motrix-intro-landscape-1080p.mp4` | Horizontal introduction |
| `Real2Motrix-intro-portrait-1080p.mp4` | Vertical introduction |
| `Real2Motrix.zh-CN.srt` | Chinese subtitles |
| `cover-landscape.png`, `cover-portrait.png` | Original covers |
| `original-geometry-motrix.zip` | Validated synthetic asset package |
| `evidence.json`, `browser-evidence.json` | API/worker and browser evidence |

## Reproduce

Use an isolated database and output directory. Do not point a recording run at
your personal capture library. Set these variables in both backend terminals:

```bash
export REAL2MOTRIX_DATABASE_PATH="$PWD/artifacts/launch/runtime/database.sqlite3"
export REAL2MOTRIX_DATA_DIR="$PWD/artifacts/launch/runtime/data"
export REAL2MOTRIX_OUTPUT_DIR="$PWD/artifacts/launch/runtime/outputs"
export REAL2MOTRIX_PORT=8010
export REAL2MOTRIX_CORS_ORIGINS='["http://127.0.0.1:5174"]'
```

Start the API and worker as described in the root README. Start the frontend
with `VITE_API_BASE_URL=http://127.0.0.1:8010 npm run dev -- --port 5174`.
From the repository root:

```bash
.venv/bin/python scripts/launch_demo.py
# Requires Playwright and its Chromium browser in your Node environment.
node scripts/record_launch.cjs
# macOS, FFmpeg/FFprobe, Pillow and a Chinese font are required.
.venv/bin/python scripts/render_launch_video.py
```

Inspect the entire video before publishing. Check audio, subtitle timing,
overlap, any machine-local paths and all capability claims. The renderer only
distributes a cropped fullscreen section of the raw browser recording; raw
recordings and runtime databases are not release assets.

## Verified on 2026-10-26

- Python 3.12: 17 backend tests passed after dependency updates.
- Node 24: 17 frontend tests passed, including 4 path-display regression tests.
- `npm audit` and requirements-based `pip-audit`: no known vulnerabilities.
- Gitleaks: 11 fetched history commits, including the launch changes, scanned;
  no detected credentials.
- Original geometry passed the actual HTTP API/worker path and package validation:
  3 object candidates, XML/URDF/JSON/ZIP files. This demonstrates packaging only.
- Browser: fullscreen preview rendered, orbit changed pixels, no page errors.

The first recorded HTTP run used the pre-existing Python 3.9 development
environment; upgraded requirements were checked separately under Python 3.12.
Optional COLMAP/OpenMVS/Open3D dependencies, true surface coverage, real iPhone
capture, app signing and physical simulation acceptance were not validated by
this launch run. Do not interpret format checks as target-runtime acceptance.

## Launch strategy

1. Publish an honest Alpha with a reproducible example and failure boundaries.
2. Gather real-device reports with licensed inputs and measurable quality.
3. Publish comparison videos only after scene/object benchmarks are reproducible.
4. Invite focused contributions through the roadmap; do not promise star counts.

Platform descriptions: [publishing copy](platform-copy.md). Uploading, processing,
approval and public availability are distinct states; only a verified public
link establishes that a platform publication is complete.
