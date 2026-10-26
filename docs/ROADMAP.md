# Roadmap and acceptance criteria

Real2Motrix is an Alpha local capture and asset-processing workbench. The goal is
a reproducible path from captured geometry to inspectable simulation assets.
This roadmap is not a claim that the following work is already complete.

## Available in source

- Native iOS ARKit capture client and live upload endpoints.
- Desktop task management, Chinese/English UI, 3D visual/collision preview.
- Mesh cleanup, geometric object candidates, MJCF/URDF packaging and validation.
- Optional COLMAP/OpenMVS image/video reconstruction path.

## Before a wider launch

1. **Real-device acceptance:** record a consented phone-to-desktop capture,
   reconnect, resume, finish and export session. Retain device/version evidence.
2. **Coverage quality:** replace trajectory-grid occupancy with observed-surface
   coverage and uncertainty. Current percentages are not scene completeness.
3. **Reconstruction benchmark:** publish licensed indoor-scene and object inputs,
   camera calibration, scale error, failure cases, timings and memory usage.
4. **Simulation acceptance:** load exported packages into the target runtime and
   test contacts, units, object transforms and physical parameters. Format
   validation alone does not establish physics correctness.
5. **Network hardening:** authentication, authorization, upload/archive limits,
   session expiry and resource isolation before supporting shared deployments.

## Research track

- Treat scene reconstruction and object reconstruction as distinct pipelines.
- Improve alignment using calibration, pose/depth confidence and scale anchors.
- Evaluate 3D Gaussian Splatting for appearance separately from collision meshes.
  The current code does not train or render Gaussian splats.
- Track reconstruction quality, not stars, as the primary technical metric.

## Useful first contributions

Small reproducible failing meshes; iOS device compatibility reports; collision
quality regression cases; documentation fixes; test coverage for interrupted jobs.
Open an issue describing the intended change before starting a large redesign.
