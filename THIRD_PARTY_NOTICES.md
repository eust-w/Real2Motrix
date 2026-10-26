# Third-party notices

The root Apache-2.0 license applies to original repository code and newly created SVG/demo assets. It does not relicense third-party dependencies, model weights, datasets, imported user assets, or externally referenced material.

Dependency versions are recorded in `frontend/package-lock.json` and Python requirements. Retain upstream copyright and license notices when redistributing dependencies. No external model weights are added by this release.

Optional tools are installed separately and are not relicensed by this repository:

| Component | Upstream license / source |
| --- | --- |
| COLMAP | BSD-3-Clause: https://github.com/colmap/colmap |
| OpenMVS | AGPL-3.0: https://github.com/cdcseacave/openMVS |
| Open3D | MIT: https://github.com/isl-org/Open3D |
| Blender | GPL: https://www.blender.org/about/license/ |

Review the exact versions and their dependencies before bundling executables,
containers or hosted services. Subprocess invocation does not change an upstream
license. This table is not a complete transitive license audit or legal opinion.

`discoverse-dev/gs_playground` was studied as a reference; Real2Motrix does not
claim its results or ship its Gaussian Splatting implementation. Demo geometry
created by the repository scripts is synthetic, not reconstructed footage.
