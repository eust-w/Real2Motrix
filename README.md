<div align="center">
  <img src="docs/readme/hero.svg" width="100%" alt="Real2Motrix workflow overview">
  <h1>Real2Motrix</h1>
  <p><strong>Capture the real world. Export a simulation scene.</strong></p>
  <p><a href="LICENSE"><img alt="License: Apache-2.0" src="https://img.shields.io/badge/License-Apache--2.0-d99536?style=flat-square"></a> <a href="docs/readme/validation.md"><img alt="Validation notes" src="https://img.shields.io/badge/Validation-repository%20checks-547ac4?style=flat-square"></a></p>
  <p><a href="#overview">Overview</a> · <a href="#quick-start">Quick start</a> · <a href="#workflow">Workflow</a> · <a href="#validation">Validation</a> · <a href="#documentation">Docs</a></p>
  <p><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a></p>
</div>

---

<a id="overview"></a>
## Overview

A local toolchain for ARKit capture, mesh processing and MJCF / URDF scene packaging. Start with an original synthetic mesh, then add reconstruction tools as your input type requires.

| Capability | What it provides |
| :--- | :--- |
| **Native capture** | SwiftUI / ARKit source; real devices require Xcode and signing. |
| **Local processing** | FastAPI, SQLite and an independent Python worker. |
| **Scene export** | Visual/collision meshes, MJCF, URDF, metadata and ZIP validation. |

### Local demo

![Real2Motrix synthetic mesh export](docs/readme/demo.jpg)

*Original synthetic mesh exported and validated through the local API and worker.*

<a id="quick-start"></a>
## Quick start

```bash
git clone https://github.com/eust-w/Real2Motrix.git
cd Real2Motrix
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
python scripts/synthetic_demo.py
```

<a id="workflow"></a>
## Workflow

```text
CAPTURE → RECONSTRUCT → EXPORT
```

```bash
# In separate terminals, with the virtual environment active:
cd backend && python -m app.main
cd backend && python -m app.worker
cd frontend && npm ci && npm run dev
```

<a id="validation"></a>
## Validation

```bash
cd backend && ../.venv/bin/python -m pytest
cd ../frontend && npm test && npm run build
```

Recorded environment and executed checks: [validation notes](docs/readme/validation.md).

| Area | Current boundary |
| :--- | :--- |
| Synthetic mesh | The bundled demo creates original geometry and validates XML / URDF / JSON / ZIP. |
| Reconstruction | COLMAP / OpenMVS / Blender / Open3D are optional native dependencies; image tests using fake commands do not verify real reconstruction. |
| iOS | Real-device capture, signing and TestFlight are separate acceptance steps. |

<a id="documentation"></a>
## Docs

- [Pipeline / 流水线](backend/app/pipeline/full_pipeline.py)
- [Backend tests / 后端测试](backend/tests/)
- [iOS release / iOS 发布](docs/ios-release.md)

## License and provenance

Original code and newly created demo assets are licensed under [Apache-2.0](LICENSE). Dependencies, models, datasets and external resources retain their terms; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
