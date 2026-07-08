---
name: okta-authenticators
description: Read Okta authenticator configuration — enrolled authenticator types, their methods, and custom Passkey/WebAuthn AAGUIDs. Use when asked what MFA/authenticator options are enabled org-wide, or to look up a specific authenticator's methods or trusted security key models.
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
compatibility: Requires Python 3.8+ and uv (preferred) or the requests library. Requires OKTA_CLIENT_ORGURL and auth environment variables. All operations in this skill are ⚠️ Limited GA (`isGenerallyAvailable: false`) per the OpenAPI spec — org support may vary.
allowed-tools: Bash
---

## Operations

```bash
uv run skills/okta-authenticators/scripts/authenticators.py <command> [options]
```

### list / get
List all authenticators configured in the org, or get one by ID.
```bash
uv run skills/okta-authenticators/scripts/authenticators.py list
uv run skills/okta-authenticators/scripts/authenticators.py get aut1nd8PQhGcQtSxB0g4
```

### list-methods / get-method
List the methods available for an authenticator, or get one by type (e.g. `sms`, `push`, `webauthn`).
```bash
uv run skills/okta-authenticators/scripts/authenticators.py list-methods aut1nd8PQhGcQtSxB0g4
uv run skills/okta-authenticators/scripts/authenticators.py get-method aut1nd8PQhGcQtSxB0g4 webauthn
```

### list-aaguids / get-aaguid
List custom Passkey (FIDO2 WebAuthn) AAGUIDs registered for an authenticator, or get one by AAGUID.
```bash
uv run skills/okta-authenticators/scripts/authenticators.py list-aaguids aut1nd8PQhGcQtSxB0g4
uv run skills/okta-authenticators/scripts/authenticators.py get-aaguid aut1nd8PQhGcQtSxB0g4 cb69481e-8ff7-4039-93ec-0a272911111
```

## Environment Variables

| Variable | Description |
|---|---|
| `OKTA_CLIENT_ORGURL` | Your Okta org URL, e.g. `https://example.okta.com` |
| `OKTA_CLIENT_TOKEN` | Okta API token with read permissions |
| `OKTA_CLIENT_CONNECTIONTIMEOUT` | Connection timeout in seconds (default: 30) |
| `OKTA_CLIENT_REQUESTTIMEOUT` | Request/read timeout in seconds (default: 30) |

## Output

JSON to stdout. `list`-prefixed commands return arrays; `get`-prefixed commands return a single object. Errors are JSON with an `error` key on stderr; exit code 1.

## Notes

Only custom AAGUIDs that an admin has explicitly created are returned by `list-aaguids`/`get-aaguid` — this is not the full FIDO Alliance AAGUID registry, just the org's own additions.

## Output Schema

### Authenticator object (`list` / `get`)

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier for the authenticator |
| `key` | string | Machine-readable authenticator identity, e.g. `okta_verify`, `phone_number`, `webauthn`, `security_key`, `okta_password`, `google_otp`, `duo`, `security_question`, `okta_email`, `custom_app`, `custom_otp`, `onprem_mfa`, `external_idp`, `symantec_vip`, `smart_card_idp`, `yubikey_token`, `tac` |
| `type` | string | Broader category: `app`, `email`, `federated`, `password`, `phone`, `security_key`, `security_question`, `tac` |
| `name` | string | Display name shown to end users |
| `status` | string | `ACTIVE` or `INACTIVE` |
| `description` | string | Description (only set for `webauthn`/Passkeys) |
| `created` / `lastUpdated` | ISO 8601 string | Timestamps |

### Method object (`list-methods` / `get-method`)

| Field | Type | Description |
|---|---|---|
| `type` | string | Method type: `cert`, `duo`, `email`, `idp`, `otp`, `password`, `push`, `security_question`, `signed_nonce`, `sms`, `totp`, `voice`, `webauthn`, `tac` |
| `status` | string | `ACTIVE` or `INACTIVE` |

An authenticator can support multiple methods (e.g. the phone authenticator has both `sms` and `voice` methods) — each has its own independent status.

### Custom AAGUID object (`list-aaguids` / `get-aaguid`)

| Field | Type | Description |
|---|---|---|
| `aaguid` | string | The 128-bit Authenticator Attestation GUID identifying a specific security key/authenticator model |
| `name` | string | Product name associated with the AAGUID |
| `authenticatorCharacteristics.fipsCompliant` | boolean | Whether the device meets FIPS compliance |
| `authenticatorCharacteristics.hardwareProtected` | boolean | Whether the private key is stored in a hardware component |
| `authenticatorCharacteristics.platformAttached` | boolean | Whether the AAGUID is built into the device (`true`) vs. an external/removable authenticator |
| `attestationRootCertificates` | object | Root certificates used to verify attestation for this AAGUID |

## Interpretation

### What to look for

- **Inactive but present authenticators**: `status: INACTIVE` on an authenticator from `list`/`get` means it's configured but not usable for enrollment or verification — distinguish this from an authenticator that's simply absent from the list.
- **Weak-factor exposure**: An org with `security_question` or `okta_email` active alongside phishing-resistant options (`webauthn`, `okta_verify` with `signed_nonce`) may still let users fall back to weaker factors — check each method's `status` under `list-methods`, not just the authenticator's own status.
- **Method-level granularity**: A single authenticator's overall `status` can be `ACTIVE` while an individual method is `INACTIVE` (e.g. `phone_number` active but `voice` disabled, `sms` enabled) — always check `list-methods` when asked "is X available," don't infer it from the authenticator alone.
- **Custom AAGUID scope restriction**: A non-empty `list-aaguids` result means the org has restricted Passkey/security-key enrollment to specific hardware models — absence of an entry doesn't necessarily mean a key is blocked, it depends on how the associated authenticator's policy references these AAGUIDs.

### Cross-skill references

- Authenticator `key`/`type` values correspond to the `factor` conditions referenced in `okta-policies` sign-on and MFA enrollment policy rules — cross-reference `okta-policies get-rule` to see which authenticators a policy requires or allows
- Authenticator changes and enrollment events surface in `okta-logs` under event types like `system.mfa.factor.deactivate`, `system.mfa.factor.activate`, and `policy.rule.update` — filter with `eventType sw "system.mfa."`
