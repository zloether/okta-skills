---
name: okta-groups
description: Read Okta groups and group memberships. Use when asked about groups, which users belong to a group, which groups a user is a member of, or to list all groups in the org.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+, the requests library, and OKTA_CLIENT_ORGURL and OKTA_CLIENT_TOKEN environment variables.
allowed-tools: Bash
---

## Operations

```bash
python skills/okta-groups/scripts/groups.py <command> [options]
```

### list
List groups, optionally filtered.
```bash
python skills/okta-groups/scripts/groups.py list
python skills/okta-groups/scripts/groups.py list --filter 'type eq "OKTA_GROUP"'
```

### get
Get a single group by ID.
```bash
python skills/okta-groups/scripts/groups.py get 00g1ab2cd3EF4GH5IJ6K
```

### get-members
List all users that are members of a group.
```bash
python skills/okta-groups/scripts/groups.py get-members 00g1ab2cd3EF4GH5IJ6K
```

### search
Search groups by name.
```bash
python skills/okta-groups/scripts/groups.py search "Admins"
python skills/okta-groups/scripts/groups.py search "Engineering"
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. List and `get-members` return arrays; `get` returns a single group object. Errors are JSON with an `error` key on stderr; exit code 1.

## Filter Reference

Common SCIM filter expressions for `--filter`:
- `type eq "OKTA_GROUP"` — manually managed groups
- `type eq "APP_GROUP"` — groups pushed from an app
- `type eq "BUILT_IN"` — built-in groups (e.g. Everyone)
