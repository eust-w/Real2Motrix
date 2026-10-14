# Release validation

Date: 2026-10-14. Checks are executed in an isolated working checkout. Screenshots use local synthetic/demo data. A source implementation, a passing automated test and external-service acceptance are separate claims.

## Commands

```bash
cd backend && ../.venv/bin/python -m pytest
cd ../frontend && npm test && npm run build
```

PASS: 17 backend tests; frontend tests and build; original mesh CLI export; real local API/worker job completed and package validation returned valid. iOS capture and real photo reconstruction were not exercised. Hardware, external credentials, signing and production deployment are separate setup/acceptance steps.
