---
name: okta-policies
description: Read Okta policies and policy rules including sign-on, MFA enrollment, password, and access policies. Use when asked about authentication policies, MFA requirements, password requirements, session lifetimes, or policy rule configurations.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+, the requests library, and OKTA_CLIENT_ORGURL and OKTA_CLIENT_TOKEN environment variables.
allowed-tools: Bash
---

## Operations

```bash
python skills/okta-policies/scripts/policies.py <command> [options]
```

### list
List policies by type. `--type` is required by the Okta API.
```bash
python skills/okta-policies/scripts/policies.py list --type OKTA_SIGN_ON
python skills/okta-policies/scripts/policies.py list --type MFA_ENROLL
python skills/okta-policies/scripts/policies.py list --type PASSWORD
python skills/okta-policies/scripts/policies.py list --type ACCESS_POLICY
```

### get
Get a single policy by ID.
```bash
python skills/okta-policies/scripts/policies.py get 00p1ab2cd3EF4GH5IJ6K
```

### get-rules
List all rules for a policy.
```bash
python skills/okta-policies/scripts/policies.py get-rules 00p1ab2cd3EF4GH5IJ6K
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. List operations return arrays; `get` returns a single policy object. Errors are JSON with an `error` key on stderr; exit code 1.

## Policy Type Reference

| Type | Description |
|---|---|
| `OKTA_SIGN_ON` | Global session and authentication policies |
| `MFA_ENROLL` | MFA enrollment policies |
| `PASSWORD` | Password policies |
| `ACCESS_POLICY` | App sign-on (access) policies |
| `PROFILE_ENROLLMENT` | Profile enrollment policies |
| `IDP_DISCOVERY` | IdP routing/discovery policies |
| `OAUTH_AUTHORIZATION_POLICY` | OAuth 2.0 authorization server policies |
