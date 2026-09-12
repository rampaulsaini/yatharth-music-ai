# Security Policy

## Scope

Yatharth Music AI is an open-source project. Security reports should focus on vulnerabilities in this repository, its API, deployment configuration, or documented integration patterns.

## Reporting

Please do not publish exploitable secrets, credentials, private URLs, or a complete proof-of-concept for an unpatched vulnerability in a public issue.

For now, use a private GitHub security report if the repository account provides GitHub Security Advisories. If that channel is unavailable, open a minimal issue asking for a private reporting route without disclosing sensitive details.

## Secret handling

- Never commit `ACESTEP_API_KEY`, passwords, tokens, private keys, or provider credentials.
- Keep engine credentials on the server side.
- Use exact production CORS origins rather than `*`.
- Keep GitHub Actions permissions least-privileged.
- Do not expose ACE-Step directly to an untrusted public browser client.

## Production status

The repository is still a development/application baseline. Before operating a public commercial service, add durable authentication, authorization, per-user quotas, abuse controls, persistent task storage, secure audio storage, logging/monitoring, backups, and a security review.
