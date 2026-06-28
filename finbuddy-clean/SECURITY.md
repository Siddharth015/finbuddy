# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in FinBuddy, please report it
**privately**. Do not open a public GitHub issue.

- Use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability)
  ("Report a vulnerability" under the Security tab), or
- Contact the maintainers directly.

Please include:

- A description of the issue and its impact
- Steps to reproduce
- Any relevant logs or proof-of-concept (avoid sharing real secrets)

We aim to acknowledge reports within a few days and will keep you updated on
remediation progress.

## Handling secrets

FinBuddy never commits secrets. Configure them via environment variables:

- `BOT_TOKEN` — Telegram bot token
- `GROQ_API_KEY` — AI provider key
- `WEBHOOK_SECRET` — shared secret validating Telegram webhook calls
- `DATABASE_URL` — database credentials

All Mini App API requests are authenticated by verifying the HMAC signature of
Telegram `initData` against `BOT_TOKEN`, so the backend never trusts a
client-supplied user id.
