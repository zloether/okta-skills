# Security Policy

Every skill in this repository is **read-only** — all requests are `GET`s against the Okta Management API. No skill creates, modifies, or deletes any resource in your Okta org.

## Read-only does not mean non-sensitive

Some read-only endpoints return live, usable secrets, not just metadata. In particular:

- `okta-apps list-secrets` returns app client secrets in cleartext.
- `okta-identity-providers list-tokens` returns usable third-party OAuth tokens.
- `okta-users get-client-tokens` returns OAuth refresh tokens.

Because these skills are typically invoked by an AI agent, this output can end up in a conversation transcript or a model provider's logs, not just your terminal. Avoid running these specific commands in contexts where that's a concern, and treat their output with the same care you'd give the credential itself.

## Reporting a Vulnerability

Please use [GitHub's private vulnerability reporting](https://github.com/zloether/okta-skills/security/advisories/new) rather than opening a public issue.
