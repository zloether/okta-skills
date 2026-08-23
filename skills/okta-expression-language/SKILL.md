---
name: okta-expression-language
description: Reference for Okta Expression Language (EL) syntax, attributes, and functions. Use whenever a policy rule or group rule contains a custom expression that needs to be read, explained, or evaluated against user/device/session data — e.g. `elCondition.condition` on an Authentication Policy or Okta Account Management Policy rule (from `okta-policies`), or `conditions.expression.value` on a group rule (from `okta-groups`).
license: Apache-2.0 WITH Commons-Clause. See LICENSE for complete terms.
---

## Two dialects — do not mix syntax

Okta Expression Language is based on a subset of [Spring Expression Language (SpEL)](https://docs.spring.io/spring-framework/reference/core/expressions.html) but ships as two distinct, non-interchangeable dialects. Identify which one you're reading before interpreting it — the same operation is written differently in each.

| Where it appears | Field | Dialect |
|---|---|---|
| Authentication Policy rule, Okta Account Management Policy rule (both are `ACCESS_POLICY` type) | `okta-policies get-rule` → `conditions.elCondition.condition` | **Identity Engine EL** — method-call syntax |
| Group rule | `okta-groups get-rule` → `conditions.expression.value` | **Classic EL** — function-call syntax, restricted function set |
| Profile mappings, IdP username transforms, OIDC custom claims (not read by any skill in this repo) | — | Classic EL |

The tell: Identity Engine EL calls functions as methods on the value (`user.profile.email.toUpperCase()`); Classic EL calls them as static functions (`String.toUpperCase(user.email)`). An expression using dot-method chaining like `.toLowerCase()` or `.withinDays(1)` is Identity Engine EL; one using `String.*`, `Arrays.*`, or `Convert.*` prefixes is Classic EL.

Both dialects use `==`/`!=` for equality, `?:` for ternary, and reject assignment (`=`), increment/decrement, and `instanceof`.

---

## Identity Engine EL (Authentication Policies & Account Management Policy)

This is the dialect for `elCondition.condition` on `ACCESS_POLICY` rules — both flavors (`resourceType: APP` and `resourceType: END_USER_ACCOUNT_MANAGEMENT`).

### Attributes

#### User

| Syntax | Description | Example |
|---|---|---|
| `user.$property` | Top-level property: `id`, `status`, `created`, `lastUpdated`, `passwordChanged`, `lastLogin` | `user.id`, `user.status` |
| `user.profile.$attribute` | Any user profile attribute, including custom-defined ones | `user.profile.firstName`, `user.profile.department` |

`user.status` cannot be used directly in **group rules** (use `user.getInternalProperty("status")` there instead — see Classic EL below) but is valid as `user.status` in Identity Engine EL policy rule expressions.

#### Device

Valid in `elCondition` on `ACCESS_POLICY` rules:

| Syntax | Type | Description |
|---|---|---|
| `device.id` | String | Okta-assigned device ID. Only populated when the user authenticates with Okta FastPass on an enrolled device. |
| `device.assurance.screenLockType` | String | `NONE`, `PASSCODE`, or `BIOMETRIC` |
| `device.caller.binaryIdentifier` | String | App allowed to invoke Okta FastPass (macOS/Windows) |
| `device.caller.bindingType` | String | `LOOPBACK` (macOS/Windows) or `APPLE_SSO_EXTENSION` (macOS) |
| `device.caller.validationStatus` | String | `SUCCESS` if the calling binary is signed |
| `device.provider.oktaVerify.version` | String | Compare with `.versionGreaterThan()` / `.versionLessThan()` or `==` |

**Not** valid in `elCondition` on policy rules — `device.profile.*` and `device.provider.*` (other than `oktaVerify`) are Identity Engine EL attributes, but scoped to federated claims only. Listed here so you can recognize them and correctly flag them as unsupported if they turn up in what looks like a policy rule condition:

| Syntax | Type | Description |
|---|---|---|
| `device.profile.$attribute` | — | Any device profile attribute, including custom-defined ones |
| `device.profile.diskEncryptionType` | String | `NONE`, `FULL`, `USER`, `ALL_INTERNAL_VOLUMES`, `SYSTEM_VOLUME` |
| `device.profile.displayName` | String | Device display name |
| `device.profile.imei` / `.meid` / `.serialNumber` / `.udid` / `.sid` | String | Hardware identifiers; not populated for every device/platform |
| `device.profile.integrityDebug` / `.integrityEmulator` / `.integrityHook` / `.integrityJailbreak` / `.integrityRepackage` | Boolean | Device integrity/tamper signals |
| `device.profile.managed` | Boolean | Requires Device Trust or the `DEVICE_CONDITION_IDX_ADVANCED` feature |
| `device.profile.manufacturer` / `.model` | String | |
| `device.profile.osVersion` | String | Compare with `.versionGreaterThan()` / `.versionLessThan()`, **not** `<`/`>` (those compare as literal strings) |
| `device.profile.platform` | String | `IOS`, `ANDROID`, `WINDOWS`, `MACOS`, `MOBILE_OTHER`, `DESKTOP_OTHER`, `CHROMEOS` |
| `device.profile.registered` | Boolean | |
| `device.profile.secureHardwarePresent` | Boolean | TPM or Secure Enclave present (doesn't check for tokens) |
| `device.profile.tpmPublicKeyHash` | String | |
| `device.provider.$vendor.$signal` | — | EDR signal, e.g. `device.provider.wsc.fireWall` (Windows Security Center), `device.provider.zta.overall` (CrowdStrike) |
| `device.provider.deviceAccess.joined` | Boolean | Device joined to Okta for Device-Bound SSO (DBSSO) |

#### Session

| Syntax | Description | Example result |
|---|---|---|
| `session.amr` | Array of [Authentication Method References](https://tools.ietf.org/html/rfc8176) used for the session | `["pwd", "otp", "mfa"]` |
| `session.id` | Unique session key | — |

#### Security context

| Syntax | Type | Values / usage |
|---|---|---|
| `security.risk.level` | String | `'LOW'`, `'MEDIUM'`, `'HIGH'` — e.g. `security.risk.level == 'HIGH'` |
| `security.behaviors` | Array of strings | Matching [behavior detection](https://help.okta.com/okta_help.htm?id=ext_proc_security_behavior_detection) signals — e.g. `security.behaviors.contains('New IP') && security.behaviors.contains('New Device')`. Cross-reference names with `okta-behaviors list`. |

#### Login context

| Syntax | Description |
|---|---|
| `login.identifier` | The user's `username` from the login context (dynamic IdP routing) |

#### Okta Account Management (`END_USER_ACCOUNT_MANAGEMENT` `ACCESS_POLICY` rules only)

| Syntax | Description |
|---|---|
| `accessRequest.$operation` | The account management operation being performed: `enroll`, `unenroll`, `recover`, or `unlockAccount` — e.g. `accessRequest.operation == 'recover'` |
| `accessRequest.authenticator.$id` | Authenticator `id`, e.g. for a Custom Authenticator |
| `accessRequest.authenticator.$key` | Authenticator key (same values as `actions.appSignOn.verificationMethod.constraints[].*.authenticationMethods[].key` in `okta-policies`) |
| `accessRequest.metadata.type` | Only used with a `recover` operation; the only supported value is `expiry` (a recovery request triggered by a password that has expired or is expiring soon) |

This is the attribute family to look for when a rule under the **Okta Account Management Policy** (`_embedded.resourceType eq "END_USER_ACCOUNT_MANAGEMENT"` in `okta-policies`) has an `elCondition` — it's the only context where `accessRequest.*` is valid.

#### Application entitlements

Not valid in `elCondition` on policy rules — `appuser.entitlements` is an Identity Engine EL attribute, but Okta's docs confirm it's scoped to federated claims and explicitly **not usable in app sign-in policy rules** (account management policy rules aren't documented as supported either). Listed here so you can recognize it and correctly flag it as unsupported if it turns up in what looks like a policy rule condition:

| Syntax | Description |
|---|---|
| `appuser.entitlements.$attribute` | Entitlement claim expression, valid only in federated claims |

### Functions

Method-call syntax: invoke on the value itself, e.g. `user.profile.firstName.toUpperCase()`.

#### String

| Function | Params | Returns | Example | Output |
|---|---|---|---|---|
| `.toUpperCase()` | — | String | `'test'.toUpperCase()` | `TEST` |
| `.toLowerCase()` | — | String | `'TEST'.toLowerCase()` | `test` |
| `.substring(start)` | int | String | `'test'.substring(1)` | `est` |
| `.substring(start, end)` | int, int (end exclusive) | String | `user.profile.firstName.substring(1,3)` | `oh` (from `John`) |
| `.replace(match, repl)` | String, String | String | `'hello'.replace('l','p')` | `heppo` |
| `.replaceFirst(match, repl)` | String, String | String | `'hello'.replaceFirst('l','p')` | `heplo` |
| `.length()` | — | Integer | `'test'.length()` | `4` |
| `.removeSpaces()` | — | String | `'This is a test'.removeSpaces()` | `Thisisatest` |
| `.contains(str)` | String | Boolean | `'This is a test'.contains('test')` | `true` (case-sensitive) |
| `.substringBefore(str)` | String | String | `user.profile.email.substringBefore('@')` | `john.doe` |
| `.substringAfter(str)` | String | String | `user.profile.email.substringAfter('@')` | `okta.com` |

#### Array

| Function | Params | Returns | Example | Output |
|---|---|---|---|---|
| `.contains(item)` | Object | Boolean | `user.profile.intArray.contains(3)` | `true` |
| `.size()` | — | Integer | `user.profile.strArray.size()` | `2` |
| `.isEmpty()` | — | Boolean | `{}.isEmpty()` | `true` |
| `.add(item)` | Object | Array | `user.profile.strArray.add('zero')` | `{"one","two","zero"}` |
| `.remove(item)` | Object | Array | `user.profile.intArray.remove(1)` | removes value `1` |
| `.flatten()` | — | Array | `user.profile.intArray.flatten()` | flattens nested arrays |

#### Conversion

| Function | Returns | Example | Output |
|---|---|---|---|
| `.toInteger()` (on String) | Integer | `'1.1'.toInteger()` | `1` |
| `.toNumber()` (on String) | Double | `'1.7'.toNumber()` | `1.7` |
| `.toInteger()` (on Number) | Integer | `1.1.toInteger()` | `1`; `-1.6.toInteger()` → `-2` |

Rounds to nearest integer; watch for integer-overflow when converting large doubles (`2147483647.7.toInteger()` wraps to `-2147483648`). `.toInteger()`/`.toNumber()` throw an exception on non-numeric input — a bare string like an email address will error, not silently return null.

**Country codes** (ISO 3166-1) — call `.parseCountryCode()` on a string (accepts Alpha-2, Alpha-3, numeric, or full name), then chain a converter:

| Function | Returns | Example | Output |
|---|---|---|---|
| `.parseCountryCode()` | CountryCode object | `user.profile.country.parseCountryCode()` | — |
| `.toAlpha2()` | String | `'USA'.parseCountryCode().toAlpha2()` | `US` |
| `.toAlpha3()` | String | `'840'.parseCountryCode().toAlpha3()` | `USA` |
| `.toNumeric()` | String | `'United States'.parseCountryCode().toNumeric()` | `840` |
| `.toName()` | String | `'US'.parseCountryCode().toName()` | `United States` |

#### Group

Search criteria are key-value pairs. Supported keys: `group.id`, `group.source.id`, `group.type` (exact match only), and `group.profile.name` (supports `EXACT` or `STARTS_WITH`, defaults to `STARTS_WITH` if `operator` is omitted). Multiple values for one key act as OR; multiple separate criteria act as AND.

| Function | Returns | Example |
|---|---|---|
| `user.getGroups($criteria...)` | Array | `user.getGroups({'group.type': {'OKTA_GROUP'}}, {'group.profile.name': {'Everyone','West Coast Admins'}})` — groups of type `OKTA_GROUP` whose name starts with `Everyone` or `West Coast Admins` |
| `user.isMemberOf($criteria...)` | Boolean | `user.isMemberOf({'group.profile.name': 'West Coast', 'operator': 'EXACT'})` |

**Collection projections** — `.![$projectionExpression]` transforms the array `user.getGroups()` returns without needing a separate lookup:

```
user.getGroups({'group.profile.name': 'Everyone'}).![id]              → group IDs
user.getGroups({'group.profile.name': 'Everyone'}).![type]            → group types
user.getGroups({'group.profile.name': 'Everyone'}).![created]         → creation timestamps
user.getGroups({'group.profile.name': 'Everyone'}).![lastUpdated]     → last-updated timestamps
user.getGroups({'group.profile.name': 'Everyone'}).![profile.name]    → group names
user.getGroups({'group.profile.name': 'Everyone'}).![profile.description] → group descriptions
```

#### Linked object

`user.getLinkedObject($primaryName)` returns the linked User for a `primary` relationship (e.g. `"manager"`), and you chain a property off the result: `user.getLinkedObject("manager").lastName`.

#### Time

All `Zoned` results are ISO 8601 / RFC 3339.

| Function | Params | Returns | Example |
|---|---|---|---|
| `DateTime.now()` | — | ZonedDateTime | Current UTC time |
| `.parseWindowsTime()` | — (on String) | ZonedDateTime | Parses a Windows/LDAP timestamp string |
| `.parseUnixTime()` | — (on String) | ZonedDateTime | Parses a Unix timestamp string |
| `.parseStringTime()` | optional format string | ZonedDateTime | `'17 June 2015 00:23:19'.parseStringTime('dd MMMM yyyy HH:mm:ss')` |
| `.toWindows()` / `.toUnix()` | — | String | Converts a ZonedDateTime to that timestamp format |
| `.toString()` | optional format string | String | `user.created.toString('MM/dd/yyyy')` |
| `.toZone(zoneId)` | String | ZonedDateTime | `DateTime.now().toZone('Asia/Tokyo')` |
| `.plusDays()` / `.plusHours()` / `.plusMinutes()` / `.plusSeconds()` | int | ZonedDateTime | Offsets forward (negative values offset backward) |
| `.minusDays()` / `.minusHours()` / `.minusMinutes()` / `.minusSeconds()` | int | ZonedDateTime | Offsets backward |
| `.withinDays()` / `.withinHours()` / `.withinMinutes()` / `.withinSeconds()` | int | Boolean | `user.created.withinDays(1)` — true if within N units of now |

Time zone IDs follow the standard Java/Joda zone list (e.g. `America/New_York`, `Asia/Tokyo`).

### Constants and operators

| Action | Example |
|---|---|
| String constant | `'Hello world'` |
| Integer constant | `1234` |
| Number constant | `3.141` |
| Boolean constant | `true` |
| Concatenate strings | `user.profile.firstName + user.profile.lastName` |
| Equality / inequality | `==` / `!=` |
| AND / OR / NOT | `&&` / `\|\|` / `!` |
| Relational | `<`, `>`, `<=`, `>=` |
| Ternary | `[Condition] ? [Value if TRUE] : [Value if FALSE]` |

### Conditional expressions

Rules that apply to any Identity Engine EL expression used as a condition:

- Must have valid syntax and evaluate to a Boolean.
- Cannot contain an assignment operator (`=`).
- Referenced user/device/session properties must exist.
- Supported: any Identity Engine EL function, `&&`, `||`, `!`, `<`, `>`, `<=`, `>=`.

Examples:

```
user.profile.country == "United States"
user.profile.intArray.contains(0)
user.profile.isContractor || user.created.withinSeconds(0)
user.profile.isContractor && user.isMemberOf({'group.profile.name': 'West Coast Users'}) ? "West coast contractors" : "Others"
```

---

## Classic EL (Group Rules)

This is the dialect for `conditions.expression.value` on group rules (`okta-groups get-rule`). Function-call syntax: `String.functionName(value, ...)` rather than method chaining.

### Restriction specific to group rules

**Group rule conditions only allow `String`, `Arrays`, and `user` expressions.** `Convert.*`, `Time.*`, and other function families are not permitted here, even if syntactically valid elsewhere in Classic EL. A rule with `status: "INVALID"` (see `okta-groups`) often means the expression uses a disallowed function or references a deleted attribute/group.

Allowed examples:
```
user.hasBadge
String.stringContains(user.email, "@example.com")
Arrays.contains(user.favoriteColors, "blue")
```
Not allowed (data-conversion function): `Convert.toInt("2018") == user.yearJoined`

`user.status` cannot be referenced directly in group rules — use `user.getInternalProperty("status")` instead (e.g. `user.getInternalProperty("status") == "ACTIVE"`).

### Attributes

| Syntax | Description | Example |
|---|---|---|
| `user.$attribute` | Okta user profile attribute | `user.firstName`, `user.email` |
| `user.getInternalProperty("id")` | User's Okta ID | — |
| `user.getInternalProperty("status")` | User status: `STAGED`, `PROVISIONED`, `ACTIVE`, `RECOVERY`, `PASSWORD_EXPIRED`, `LOCKED_OUT`, `SUSPENDED` (not `DEPROVISIONED`) | — |
| `$app.$attribute` / `appuser.$attribute` | App user profile attribute (explicit app name, or implicit in-context app) | `zendesk.firstName`, `appuser.firstName` |
| `idpuser.$attribute` | IdP user profile attribute (username-transform contexts only) | `idpuser.firstName` |
| `org.$attribute` | Org property | `org.name`, `org.subDomain` |
| `session.amr` | Array of Authentication Method References for the session | `["pwd"]`, `["mfa","pwd","kba"]` |

These broader attribute families (app, IdP, org, session) apply to Classic EL generally (profile mappings, etc.) but are **not** usable inside a group rule's `conditions.expression.value` per the restriction above — only `user.*`, `String.*`, and `Arrays.*` are.

### Functions (Classic EL)

#### String

| Function | Params | Returns | Example | Output |
|---|---|---|---|---|
| `String.append` | (str, suffix) | String | `String.append("This is", " a test")` | `This is a test` |
| `String.join` | (separator, strings...) | String | `String.join(",", "This","is","a","test")` | `This,is,a,test` |
| `String.len` | (input) | Integer | `String.len("This")` | `4` |
| `String.removeSpaces` | (input) | String | `String.removeSpaces("This is a test")` | `Thisisatest` |
| `String.replace` | (input, match, repl) | String | `String.replace("This is a test","is","at")` | `That at a test` |
| `String.replaceFirst` | (input, match, repl) | String | `String.replaceFirst("This is a test","is","at")` | `That is a test` |
| `String.startsWith` | (input, starts) | Boolean | `String.startsWith("Kiss","K")` | `true` |
| `String.stringContains` | (input, search) | Boolean | `String.stringContains("This is a test","test")` | `true` |
| `String.stringSwitch` | (input, default, key/value pairs...) | String | `String.stringSwitch("First match wins","default","absent","value1","wins","value2")` | `value2` (first matching key wins) |
| `String.substring` | (input, start, end) | String | `String.substring("This is a test", 2, 9)` | `is is a` |
| `String.substringAfter` | (input, search) | String | `String.substringAfter("abc@okta.com","@")` | `okta.com` |
| `String.substringBefore` | (input, search) | String | `String.substringBefore("abc@okta.com","@")` | `abc` |
| `String.toUpperCase` / `String.toLowerCase` | (input) | String | `String.toUpperCase("This")` | `THIS` |

Deprecated but still seen in older configs: `toUpperCase()`, `toLowerCase()`, `substringBefore()`, `substringAfter()`, `substring()` (same behavior, no `String.` prefix — not usable in group rules).

#### Array

| Function | Returns | Example | Output |
|---|---|---|---|
| `Arrays.add(array, value)` | Array | `Arrays.add(user.arrayAttribute, 40)` | `{10,20,30,40}` |
| `Arrays.remove(array, value)` | Array | `Arrays.remove(user.arrayAttribute, 20)` | `{10,30}` |
| `Arrays.clear(array)` | Array | `Arrays.clear(user.arrayAttribute)` | `{}` |
| `Arrays.get(array, position)` | — | `Arrays.get({0,1,2}, 0)` | `0` |
| `Arrays.flatten(values...)` | Array | `Arrays.flatten(10, {20,30}, 40)` | `{10,20,30,40}` |
| `Arrays.contains(array, value)` | Boolean | `Arrays.contains({10,20,30}, 10)` | `true` |
| `Arrays.size(array)` | Integer | `Arrays.size({10,20,30})`; `Arrays.size(NULL)` | `3`; `0` |
| `Arrays.isEmpty(array)` | Boolean | `Arrays.isEmpty(NULL)` | `true` |
| `Arrays.toCsvString(array)` | String | `Arrays.toCsvString({"This","is","a","test"})` | `This,is,a,test` |

Comma-separated strings are accepted as input to any `Arrays.*` function and auto-converted to an array.

#### Conversion — not usable in group rules

| Function | Returns | Example | Output |
|---|---|---|---|
| `Convert.toInt(string\|double)` | Integer | `Convert.toInt('1234')` | `1234` (rounds doubles to nearest int) |
| `Convert.toNum(string)` | Double | `Convert.toNum('3.141')` | `3.141` |
| `Iso3166Convert.toAlpha2/toAlpha3/toNumeric/toName` | String | `Iso3166Convert.toAlpha2("IND")` | `IN` |

#### Group

| Function | Returns | Params | Example |
|---|---|---|---|
| `isMemberOfGroupName` | Boolean | String | `isMemberOfGroupName("group1")` — matches across all sources; use `isMemberOfGroup` (by ID) to disambiguate duplicate-named groups |
| `isMemberOfGroup` | Boolean | Group ID | `isMemberOfGroup("00g...")` |
| `isMemberOfAnyGroup` | Boolean | Group IDs... | `isMemberOfAnyGroup("id1","id2")` |
| `isMemberOfGroupNameStartsWith` / `...Contains` / `...Regex` | Boolean | String / String / Regex | `isMemberOfGroupNameContains("admin")` |
| `getFilteredGroups` | Array | (allow-list, group_expression, limit) | `getFilteredGroups({"00g..."}, "group.name", 40)` |
| `user.getGroups` | Array | search-criteria list | Same semantics as the Identity Engine EL version above, including `.![name]` collection projection |

`isMemberOfGroup*` name-based functions and `getFilteredGroups`/`Groups.*` (`Groups.contains`, `Groups.startsWith`, `Groups.endsWith` — legacy, group-claims-only) are Classic-EL-wide but **not** part of the `user`-restricted subset allowed inside group rule conditions; `Arrays.contains(user.$groupArrayAttr, ...)` and `user.getGroups(...)` (a `user.*` call) are the group rule-safe equivalents.

#### Linked object

`user.getLinkedObject($primaryName)` — same as Identity Engine EL, e.g. `user.getLinkedObject("manager").lastName`.

#### Time — not usable in group rules

| Function | Example | Output |
|---|---|---|
| `Time.now()` / `Time.now(tz)` / `Time.now(tz, format)` | `Time.now("EST", "YYYY-MM-dd HH:mm:ss")` | Formatted current time in the given zone |
| `Time.fromWindowsToIso8601` / `Time.fromUnixToIso8601` / `Time.fromStringToIso8601` | — | Converts to ISO 8601 |
| `Time.fromIso8601ToWindows` / `Time.fromIso8601ToUnix` / `Time.fromIso8601ToString` | — | Converts from ISO 8601 |

#### Manager / assistant — not usable in group rules

| Function | Description |
|---|---|
| `getManagerUser(managerSource).$attribute` | Manager's Okta user attributes. Only `managerSource: "active_directory"` is supported. |
| `getManagerAppUser(managerSource, attributeSource).$attribute` | Manager's app-user attributes for a given app instance |
| `getAssistantUser(assistantSource).$attribute` / `getAssistantAppUser(...)` | Same, for the assistant relationship |

Doesn't trigger a profile update when the manager changes; not supported across multiple AD instances or multiple app instances.

#### Directory / Workday — not usable in group rules

| Function | Description |
|---|---|
| `hasDirectoryUser()` | `true` only if exactly one AD assignment exists |
| `hasWorkdayUser()` | `true` if a Workday assignment exists |
| `findDirectoryUser()` | AD app-user object, or `null` if zero/multiple assignments |
| `findWorkdayUser()` | Workday app-user object, or `null` if zero/multiple assignments |

Common pattern: `hasWorkdayUser() ? findWorkdayUser().employeeID : null`

### Constants, operators, and conditional expressions

| Action | Example |
|---|---|
| String / Integer / Number / Boolean constant | `'Hello world'`, `1234`, `3.141`, `true` |
| Array element access | `{1,2,3}[0]` or `user.arrayProperty[0]` |
| Concatenate | `user.firstName + user.lastName` |
| Ternary | `user.groupCode == 123 ? 'Sales' : 'Other'` |
| Elvis operator (`?:`) — default if null/empty | `Groups.startsWith("OKTA","TEST",100) ?: {}` |

Conditional-expression rules: valid syntax, must evaluate to Boolean, no assignment operator, only references available user/app attributes. Supported: any Classic EL function, `AND`, `OR`, `!`, `<`, `>`, `<=`, `>=`, and the deprecated `matches` operator (regex match, e.g. `user.title matches '(?i)engineer'`). **Not supported in conditions generally: Conversion, Array, and Time functions** — this is a stricter rule than plain Classic EL and is why `Arrays.*` is documented as allowed specifically for **group rules** as a named exception (see Restriction section above) while remaining unavailable in other conditional contexts like profile-mapping IF/THEN/ELSE.

Null/blank checks:
```
user.employeeNumber == null                                    → attribute was never populated
user.employeeNumber == ""                                      → attribute was populated, then cleared
user.employeeNumber != "" AND user.employeeNumber != null ? user.employeeNumber : user.nonEmployeeNumber
```

---

## Interpretation

When a policy rule or group rule carries a custom expression, don't just quote it back — resolve it against real data:

1. **Identify the dialect** using the table at the top (method-chaining vs. function-prefix syntax), then find each referenced attribute in the tables above to know its type and where it comes from.
2. **Resolve `user.*` / `user.profile.*` references** with `okta-users get <userId_or_login>` — compare the expression's expected value against the user's actual profile field.
3. **Resolve `device.*` references** with `okta-devices get <deviceId>` (note: many `device.profile.*`/`device.provider.*` signals reflect the specific authentication attempt more than the device's persistent record — cross-check against the `device` fields on the relevant `okta-logs` event when investigating a past decision, not just current device state).
4. **Resolve group functions** (`user.isMemberOf`, `user.getGroups`, `isMemberOfGroup*`, `Arrays.contains(user.$groupAttr, ...)`) with `okta-groups get-members <groupId>` or `okta-groups search` to confirm actual membership, and note the `group.type`/`group.source.id` criteria narrow which groups qualify — a name match alone isn't sufficient if a `group.type` or `group.source.id` filter is also present.
5. **Resolve `security.risk.level` / `security.behaviors`** against the `securityContext.risk.level` and behavior fields on the relevant `okta-logs` `policy.evaluate_sign_on` or `user.authentication.*` event.
6. **Resolve `accessRequest.*`** (Account Management Policy only) against the account-management event's operation type and, if present, the authenticator involved.
7. **Point-in-time evaluation applies here too** (see `okta-policies`): an expression referencing `user.profile.department` was evaluated against the user's profile *at the time of the request*, not its current value. If profile drift is suspected, search `okta-logs` for `user.account.update_profile` between the event timestamp and now.
8. **Report every attribute the expression touches**, not just the one that looks likely to have failed — expressions frequently combine multiple conditions with `&&`/`AND`, and any one of them can be the actual blocker.

## Cross-skill references

- `okta-policies get-rule` → `conditions.elCondition.condition` — read with the Identity Engine EL section above
- `okta-groups get-rule` → `conditions.expression.value` — read with the Classic EL section above, subject to the group-rule restriction (`String`, `Arrays`, `user` only)
- `user.profile.*` / `user.$attribute` references → `okta-users get <id_or_login>`
- `device.profile.*` / `device.provider.*` references → `okta-devices get <deviceId>`; cross-check point-in-time values against the matching `okta-logs` event's `device` fields
- Group membership functions → `okta-groups get-members <groupId>` or `okta-groups search`
- `security.behaviors` values → cross-reference behavior names with `okta-behaviors list`
- `accessRequest.authenticator.key` → cross-reference with `okta-authenticators list` / `list-methods <id>`
