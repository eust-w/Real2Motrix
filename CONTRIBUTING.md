# Contributing

Real2Motrix welcomes reproducible bug reports, small fixes and real-device test
results. Read [the roadmap](docs/ROADMAP.md) and [security policy](SECURITY.md) first.

## Development

Use Python 3.12 and Node 24. Follow the README setup, then run:

```bash
cd backend
../.venv/bin/python -m pytest
cd ../frontend
npm ci
npm test
npm run build
npm audit
```

For a PR, describe the problem, the smallest reproducible input, the change and
the checks actually run. Add a regression test for changed behavior. Keep runtime
data and generated media out of Git. Contributions are made under Apache-2.0;
only submit code and assets you have permission to license.

## Evidence matters

- Label original synthetic fixtures as synthetic. Do not present them as scans.
- Report capture device, LiDAR availability, lighting, input duration, dependency
  versions, processing hardware and elapsed time for reconstruction experiments.
- Separate API/unit-test results, browser tests, real-device capture and actual
  simulator execution. Passing one does not establish the others.
- Compare visual fidelity and collision geometry separately. Provide a scale
  reference and permitted source footage when claiming reconstruction quality.
- Check recordings for faces, addresses, confidential screens and private rooms
  before sharing. Prefer a minimal original fixture for public issues.
