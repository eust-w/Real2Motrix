# Security

Real2Motrix is an experimental, single-user local workbench, not a hosted service.
Use Python 3.12 and Node 24 for the tested development environment.

- Keep both servers bound to loopback by default. The API has no authentication,
  per-user isolation, upload quotas or archive expansion quotas. Do not expose it
  to the public Internet, shared Wi-Fi or untrusted uploads.
- Phone capture requires a deliberately configured trusted private network.
  Restrict access with a firewall or authenticated tunnel. Transport security and
  access control must be provided separately; CORS is not authentication.
- Process only trusted input. Native mesh/reconstruction tools parse complex
  formats and are not sandboxed. Review their licenses and security updates.
- Never commit recordings of private spaces, credentials, signing certificates,
  provisioning profiles, databases or generated capture archives.
- Run `npm audit` in `frontend` and `pip-audit -r backend/requirements-dev.txt`
  before distributing a build. A clean scan is not a complete security audit.

Report vulnerabilities using the repository's private security reporting feature
when available. Do not post exploit details, recordings or credentials in public
issues. If private reporting is unavailable, first open an issue asking for a
private contact without including the vulnerability itself.

Only the current main branch receives fixes. No production-security guarantee is
provided for the Alpha release.
