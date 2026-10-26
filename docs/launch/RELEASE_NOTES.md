# Real2Motrix v0.1.0-alpha.1

A local capture and asset-processing workbench for robotics simulation.

## Included

- React/Three.js task management and visual/collision previews, Chinese/English UI.
- FastAPI/SQLite worker, mesh processing and validated MJCF/URDF scene packages.
- Experimental native ARKit capture source and live upload endpoints.
- Original synthetic demo, reproducible launch scripts, contribution and security
  guidelines, roadmap and core CI checks.
- Updated audited dependencies and relative asset paths in the UI.

## Evidence and boundaries

17 backend tests and 17 frontend tests passed locally. Dependency audits found
no known vulnerabilities in the audited requirements and frontend lockfile.
The attached geometry package was produced by the real API/worker and validated.
See `docs/launch/README.md` for exact scope and reproduction.

The videos use original synthetic geometry, real application recording and
synthetic narration. They do not demonstrate real-phone scan quality, 3DGS or
physical simulation correctness. Real-device capture, signing and simulator
acceptance remain separate work. No signed iOS app is included in this release.

Local/trusted input only: the API is not authenticated or resource-isolated.
Read SECURITY.md before networking. Optional native dependencies retain their
upstream licenses; this release does not bundle them or private capture data.
