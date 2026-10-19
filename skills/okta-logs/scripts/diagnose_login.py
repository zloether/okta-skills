#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Mechanically diagnose one user's login failures from the Okta System Log.

Finds the user's DENY/FAILURE events, then for each distinct policy DENY walks the
policy rules named in the event and evaluates every condition, the enrollment gate and
the verified-property requirements against the data recorded on the event itself, as of
the event's timestamp. Output is JSON rows with a tri-state `pass` (true / false / null =
could not be determined by script) that an agent can summarize without re-deriving the logic.
"""
import argparse
import ipaddress
import re
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cli import add_concurrency, run
from logs import _get_path, _quote
from okta_client import get_resource, paginated_get, parallel_map

_PROPS = {  # constraint field -> value in user.authentication.verify's methodUsedVerifiedProperties
    'phishingResistant': 'PHISHING_RESISTANT',
    'hardwareProtection': 'HARDWARE_PROTECTED',
    'userVerification': 'USER_VERIFYING',
    'userPresence': 'USER_PRESENCE',
    'deviceBound': 'DEVICE_BOUND',
}


def _ts(value):
    return datetime.fromisoformat(value) if value else None


def _chk(check, required, actual, ok, note=None):
    row = {'check': check, 'required': required, 'actual': actual, 'pass': ok}
    if note:
        row['note'] = note
    return row


def _any(oks):
    return True if True in oks else (None if None in oks else False)


def _try(fn, *a):
    try:
        return fn(*a), None
    except Exception as e:  # noqa: BLE001 — a failed lookup must degrade one check to "unknown", not abort the diagnosis
        return None, str(e)


def _ver(s):
    parts = [int(x) for x in re.findall(r'\d+', s or '')]
    return tuple(parts + [0] * (4 - len(parts)))  # pad so 28 == 28.0.0

# Log events say OSX where device assurance policies say MACOS (other values already match).
_ASSURANCE_PLATFORM = {'OSX': 'MACOS', 'MAC': 'MACOS', 'CHROME_OS': 'CHROMEOS'}


def _ip_in(ip, entry):
    try:
        addr = ipaddress.ip_address(ip)
        if entry.get('type') == 'RANGE':
            lo, hi = (ipaddress.ip_address(x.strip()) for x in entry['value'].split('-'))
            return lo <= addr <= hi
        return addr in ipaddress.ip_network(entry['value'], strict=False)
    except (ValueError, KeyError, TypeError):
        return None


def _zone_hit(zone, ip, event_zone):
    if zone.get('type') == 'IP':
        return _any([_ip_in(ip, g) for g in zone.get('gateways') or []])
    # Dynamic zones depend on geo/ASN/proxy data the script can't re-derive; trust the event's recorded zone name.
    return True if event_zone and event_zone == zone.get('name') else None


class _Lookups:
    """Memoized read-only API lookups; a failure is cached and re-raised so callers degrade to `pass: null`."""

    def __init__(self, session, base_url, concurrency):
        self.session, self.base, self.concurrency = session, base_url, concurrency
        self._cache = {}

    def _memo(self, key, fn):
        if key not in self._cache:
            try:
                self._cache[key] = (fn(), None)
            except Exception as e:  # noqa: BLE001 — see _try
                self._cache[key] = (None, e)
        value, err = self._cache[key]
        if err:
            raise err
        return value

    def _pp(self, **ids):
        return {'base': self.base, **ids}

    def policies(self, ptype):
        return self._memo(('policies', ptype), lambda: paginated_get(self.session, '{base}/api/v1/policies', {'type': ptype}, path_params=self._pp()))

    def policy(self, pid):
        return self._memo(('policy', pid), lambda: get_resource(self.session, '{base}/api/v1/policies/{id}', path_params=self._pp(id=pid)))

    def rules(self, pid):
        return self._memo(('rules', pid), lambda: sorted(
            paginated_get(self.session, '{base}/api/v1/policies/{id}/rules', path_params=self._pp(id=pid)), key=lambda r: r.get('priority') or 0))

    def zones(self):
        return self._memo('zones', lambda: {z['id']: z for z in paginated_get(self.session, '{base}/api/v1/zones', path_params=self._pp())})

    def assurance(self, aid):
        return self._memo(('assurance', aid), lambda: get_resource(self.session, '{base}/api/v1/device-assurances/{id}', path_params=self._pp(id=aid)))

    def group(self, gid):
        return self._memo(('group', gid), lambda: get_resource(self.session, '{base}/api/v1/groups/{id}', path_params=self._pp(id=gid)))

    def user(self, uid):
        return self._memo(('user', uid), lambda: get_resource(self.session, '{base}/api/v1/users/{id}', path_params=self._pp(id=uid)))

    def user_groups(self, uid):
        return self._memo(('ugroups', uid), lambda: {g['id'] for g in paginated_get(self.session, '{base}/api/v1/users/{id}/groups', path_params=self._pp(id=uid))})

    def enrollments(self, uid):
        return self._memo(('enroll', uid), lambda: get_resource(self.session, '{base}/api/v1/users/{id}/authenticator-enrollments', path_params=self._pp(id=uid)))

    def authenticators(self):
        return self._memo('authenticators', lambda: {a['key']: a for a in paginated_get(self.session, '{base}/api/v1/authenticators', path_params=self._pp())})

    def methods(self, aid):
        return self._memo(('methods', aid), lambda: {m['type']: m for m in paginated_get(self.session, '{base}/api/v1/authenticators/{id}/methods', path_params=self._pp(id=aid))})

    def group_label(self, gid):
        group, _ = _try(self.group, gid)
        return (group or {}).get('profile', {}).get('name') or gid

    def find_rule(self, rule_id, policy_name):
        """Locate a rule with no detailEntry.policyId (OKTA_SIGN_ON / MFA_ENROLL) by scanning those policy types."""
        for ptype in ('OKTA_SIGN_ON', 'MFA_ENROLL'):
            policies, _ = _try(self.policies, ptype)
            policies = sorted(policies or [], key=lambda p: p.get('name') != policy_name)
            for p, rules in zip(policies, parallel_map(lambda p: self.rules(p['id']), policies, self.concurrency)):
                match = None if isinstance(rules, Exception) else next((r for r in rules if r['id'] == rule_id), None)
                if match:
                    return p, rules, match
        return None


class _Ev:
    """Everything a check needs about one DENY event."""

    def __init__(self, event, lk, user, user_groups, verify_events, mfa_policy):
        self.event, self.lk, self.user, self.user_groups = event, lk, user, user_groups
        self.verify_events, self.mfa_policy = verify_events, mfa_policy
        self.t = _ts(event.get('published'))
        self.device = event.get('device') or {}


# ---------------------------------------------------------------------------
# Condition checks — each returns a list of rows
# ---------------------------------------------------------------------------

def _network(cond, ev):
    ip, zone_name = _get_path(ev.event, 'client.ipAddress'), _get_path(ev.event, 'client.zone')
    actual = f'{ip} (zone: {zone_name})'
    if cond.get('connection') in (None, 'ANYWHERE'):
        return [_chk('network', 'ANYWHERE', actual, True)]
    zones, err = _try(ev.lk.zones)
    note = f'zones could not be read: {err}' if err else None
    rows = []
    for side in ('include', 'exclude'):
        ids = cond.get(side) or []
        if not ids:
            continue
        zs = [(zones or {}).get(i) for i in ids]
        hits = [_zone_hit(z, ip, zone_name) if z else None for z in zs]
        if side == 'include':
            ok = _any(hits)
        else:
            ok = False if True in hits else (None if None in hits else True)
        rows.append(_chk(
            f'network.{side}', ('in one of: ' if side == 'include' else 'not in: ') + ', '.join(z['name'] if z else i for z, i in zip(zs, ids)),
            actual, ok,
            note or ('dynamic zone: matched only by the event\'s recorded client.zone' if ok is None else None),
        ))
    return rows


def _people(cond, ev):
    g, u = cond.get('groups') or {}, cond.get('users') or {}
    gi, ge = set(g.get('include') or []), set(g.get('exclude') or [])
    ui, ue = set(u.get('include') or []), set(u.get('exclude') or [])
    ug, uid = ev.user_groups, ev.user.get('id')
    in_g = (lambda ids: None if ug is None else bool(ids & ug))
    note = None if ug is not None else 'user group membership could not be read'
    names = lambda ids: ', '.join(ev.lk.group_label(i) for i in sorted(ids))
    rows = []
    if gi or ui:
        by_group = in_g(gi) if gi else False
        ok = True if (uid in ui or by_group) else (None if by_group is None else False)
        required = ' / '.join(x for x in (f'groups: {names(gi)}' if gi else '', f'users: {sorted(ui)}' if ui else '') if x)
        rows.append(_chk('people.include', f'user in {required}', f'member of: {names(ug & gi) if ug is not None and gi else "n/a"}', ok, note))
    if ge or ue:
        by_group = in_g(ge) if ge else False
        ok = False if (uid in ue or by_group) else (None if by_group is None else True)
        rows.append(_chk('people.exclude', f'user not in groups: {names(ge)} / users: {sorted(ue)}', f'member of: {names(ug & ge) if ug is not None and ge else "n/a"}', ok, note))
    return rows


def _user_type(cond, ev):
    user, err = _try(ev.lk.user, ev.user['id'])
    tid = ((user or {}).get('type') or {}).get('id')
    rows = []
    inc, exc = cond.get('include') or [], cond.get('exclude') or []
    if inc:
        rows.append(_chk('userType.include', f'one of {inc}', tid, None if tid is None else tid in inc, err))
    if exc:
        rows.append(_chk('userType.exclude', f'not in {exc}', tid, None if tid is None else tid not in exc, err))
    return rows


def _device(cond, ev):
    rows = []
    for field in ('registered', 'managed'):
        if cond.get(field) is None:
            continue
        actual = ev.device.get(field)
        note = None
        if not ev.device:
            actual, note = False, 'no device object on the event; treated as not registered / not managed'
        rows.append(_chk(f'device.{field}', cond[field], actual, bool(actual) == bool(cond[field]), note))
    ids = (cond.get('assurance') or {}).get('include') or []
    if ids:
        rows += _assurance(ids, ev)
    return rows


def _integrator_errors(ev):
    text = str(ev.device.get('device_integrator') or '')
    for t in ev.event.get('target') or []:
        if t.get('type') == 'UDDevice':
            text += str((t.get('detailEntry') or {}).get('deviceIntegrator') or '')
    return re.findall(r'genericError\([^)]*\)', text)


def _assurance(ids, ev):
    dev = ev.device
    platform = (dev.get('os_platform') or '').upper()
    platform = _ASSURANCE_PLATFORM.get(platform, platform)
    groups = []  # one row list per listed policy; the rule needs only ONE of them to be satisfied
    for aid in ids:
        pol, err = _try(ev.lk.assurance, aid)
        if err:
            groups.append((aid, [_chk(f'assurance {aid}', 'policy readable', None, None, err)]))
            continue
        label = f'assurance "{pol.get("name")}"'
        if (pol.get('platform') or '').upper() != platform:
            continue
        rows = []
        om = (pol.get('osVersion') or {}).get('minimum')
        if om:
            actual = dev.get('os_version')
            rows.append(_chk(f'{label}: osVersion.minimum', om, actual, _ver(actual) >= _ver(om) if actual else None))
        elif pol.get('osVersion', {}).get('dynamicVersionRequirement') or pol.get('osVersionConstraints'):
            rows.append(_chk(f'{label}: osVersion', 'dynamic/per-major requirement', dev.get('os_version'), None, 'depends on current latest releases; not evaluated by script'))
        for key, field in (('diskEncryptionType', 'disk_encryption_type'), ('screenLockType', 'screen_lock_type')):
            inc = (pol.get(key) or {}).get('include') or []
            if inc:
                actual = dev.get(field)
                rows.append(_chk(f'{label}: {key}', inc, actual, None if actual is None else actual.upper() in {i.upper() for i in inc}, 'strict match; Okta may accept stronger values' if actual and actual.upper() not in {i.upper() for i in inc} else None))
        if pol.get('secureHardwarePresent') is not None:
            actual = dev.get('secure_hardware_present')
            rows.append(_chk(f'{label}: secureHardwarePresent', pol['secureHardwarePresent'], actual, None if actual is None else bool(actual) == bool(pol['secureHardwarePresent'])))
        if pol.get('jailbreak') is False:
            actual = dev.get('jailbreak')
            rows.append(_chk(f'{label}: jailbreak', 'not jailbroken', actual, None if actual is None else not actual))
        if pol.get('thirdPartySignalProviders') or (pol.get('devicePostureChecks') or {}).get('include'):
            errs = _integrator_errors(ev)
            rows.append(_chk(
                f'{label}: third-party signals', 'readable integrator signals', '; '.join(errs) or 'not evaluated by script',
                False if errs else None, 'an unreadable signal fails the check' if errs else 'integrator values are not compared by script',
            ))
        groups.append((f'"{pol.get("name")}"', rows))
    if not groups:
        if platform:
            return [_chk('device.assurance', f'a listed policy for platform {platform}', 'none of the listed policies cover this platform', False)]
        return [_chk('device.assurance', 'a listed policy matching the device platform', None, None, 'event carries no device platform, so coverage cannot be determined')]
    met = next((name for name, g in groups if _status(g) == 'would_allow'), None)
    if met:
        return [_chk('device.assurance', 'any one listed policy', f'met {met}', True)]
    # Not met: show the closest policy (fewest failures, then fewest unknowns).
    return min((g for _, g in groups), key=lambda g: (sum(r['pass'] is False for r in g), sum(r['pass'] is None for r in g)))


_UA_OS = (('mac', 'MACOS'), ('windows', 'WINDOWS'), ('ios', 'IOS'), ('iphone', 'IOS'), ('ipad', 'IOS'), ('android', 'ANDROID'), ('chrome', 'CHROMEOS'), ('linux', 'LINUX'))


def _platform(cond, ev):
    os_actual = (ev.device.get('os_platform') or '').upper()
    if not os_actual:
        ua = (_get_path(ev.event, 'client.userAgent.os') or '').lower()
        os_actual = next((v for k, v in _UA_OS if k in ua), '')
    kind = {'computer': 'DESKTOP', 'mobile': 'MOBILE'}.get((_get_path(ev.event, 'client.device') or '').lower())
    actual = f'{os_actual or "unknown"} / {kind or "unknown"}'
    if not os_actual and not kind:
        return [_chk('platform', 'platform condition', actual, None, 'event carries no platform info')]

    def match(entry):
        e_os = ((entry.get('os') or {}).get('type') or 'ANY').upper()
        e_kind = (entry.get('type') or 'ANY').upper()
        oks = [e_os == 'ANY' or (os_actual and e_os == os_actual) or (None if not os_actual else False),
               e_kind == 'ANY' or (kind and e_kind == kind) or (None if not kind else False)]
        return False if False in oks else (None if None in oks else True)

    rows = []
    for side in ('include', 'exclude'):
        entries = cond.get(side) or []
        if entries:
            hit = _any([match(e) for e in entries])
            ok = hit if side == 'include' else (None if hit is None else not hit)
            versioned = any((e.get('os') or {}).get('version') for e in entries)
            rows.append(_chk(f'platform.{side}', [f'{(e.get("os") or {}).get("type", "ANY")}/{e.get("type", "ANY")}' for e in entries], actual, ok, 'OS version expression not evaluated' if versioned else None))
    return rows


def _risk(cond, ev):
    want = (cond.get('level') or 'ANY').upper()
    actual = _get_path(ev.event, 'securityContext.risk.level')
    if actual is None:
        m = re.search(r'level=(\w+)', str(_get_path(ev.event, 'debugContext.debugData.risk') or ''))
        actual = m.group(1) if m else None
    if want == 'ANY':
        return [_chk('riskScore.level', 'ANY', actual, True)]
    if actual is None:
        return [_chk('riskScore.level', want, None, None, 'no risk level on the event')]
    return [_chk('riskScore.level', want, actual, actual.upper() == want)]


def _el(cond, ev):
    expr = cond.get('condition') or ''
    attrs = {m.group(1) for m in re.finditer(r'\buser\.(?:profile\.)?(\w+)(\()?', expr) if not m.group(2)}
    user, err = _try(ev.lk.user, ev.user['id'])
    profile = (user or {}).get('profile') or {}
    return [_chk('elCondition', expr, {a: profile.get(a) for a in sorted(attrs)}, None,
                 err or 'Okta Expression Language is not evaluated by script; values are as of now, not the event')]


def _app(cond, ev):
    app = next((t for t in ev.event.get('target') or [] if t.get('type') == 'AppInstance'), {})
    ids = lambda side: {a.get('id') for a in cond.get(side) or []}
    rows = []
    if ids('include'):
        rows.append(_chk('app.include', sorted(ids('include')), app.get('id'), app.get('id') in ids('include')))
    if ids('exclude'):
        rows.append(_chk('app.exclude', f'not in {sorted(ids("exclude"))}', app.get('id'), app.get('id') not in ids('exclude')))
    return rows


_CHECKS = {'network': _network, 'people': _people, 'userType': _user_type, 'device': _device,
           'platform': _platform, 'riskScore': _risk, 'elCondition': _el, 'app': _app}


def _conditions(conditions, ev):
    rows = []
    for key, cond in (conditions or {}).items():
        if not cond:
            continue
        fn = _CHECKS.get(key)
        if fn:
            rows += fn(cond, ev)
        else:
            rows.append(_chk(key, cond, None, None, 'condition type not evaluated by script'))
    return rows


# ---------------------------------------------------------------------------
# Enrollment gate and verified properties (authentication policy rules)
# ---------------------------------------------------------------------------

def _options(vm):
    """Return [(methods, required_props)] — alternatives (OR); methods are (key, method) pairs, props map field -> REQUIRED."""
    if vm.get('type') == 'ASSURANCE':
        opts = []
        for c in vm.get('constraints') or [{}]:
            methods, props = [], {}
            for part in (c.get('knowledge') or {}, c.get('possession') or {}):
                methods += [(m.get('key'), m.get('method')) for m in part.get('authenticationMethods') or []]
                props |= {f: 'REQUIRED' for f in _PROPS if part.get(f) == 'REQUIRED'}
            opts.append((methods, props))
        return opts
    if vm.get('type') == 'AUTH_METHOD_CHAIN':
        methods, props, step = [], {}, vm
        while step:
            for m in step.get('authenticationMethods') or []:
                methods.append((m.get('key'), m.get('method')))
                props |= {f: 'REQUIRED' for f in _PROPS if m.get(f) == 'REQUIRED'}
            step = (step.get('next') or [None])[0]
        return [(methods, props)]
    return None


def _verified_props(ev, key):
    """Properties of the latest user.authentication.verify for `key` (or any key if unknown) before the DENY."""
    for e in ev.verify_events:
        for t in e.get('target') or []:
            d = t.get('detailEntry') or {}
            if t.get('type') == 'AuthenticatorMethod' and (key is None or d.get('authenticatorKey') == key):
                return set(re.findall(r'[A-Z_]+', d.get('methodUsedVerifiedProperties') or ''))
    return None


def _gate(rule, ev):
    vm = ((rule.get('actions') or {}).get('appSignOn') or {}).get('verificationMethod') or {}
    opts = _options(vm)
    if opts is None:
        return [_chk('verificationMethod', vm.get('type'), None, None, 'verification method type not evaluated by script')] if vm else []
    rows = []
    enrolls, err_e = _try(ev.lk.enrollments, ev.user['id'])
    auths, err_a = _try(ev.lk.authenticators)
    settings = {a.get('key'): a for a in ((ev.mfa_policy or {}).get('settings') or {}).get('authenticators') or []}
    for n, (methods, props) in enumerate(opts, 1):
        tag = f'option {n}: ' if len(opts) > 1 else ''
        start = len(rows)
        if not methods:
            rows.append(_chk(f'{tag}authenticator methods', vm.get('type'), None, None, 'constraint names no specific authenticator method (types/methods lists are not evaluated)'))
        for key, method in methods:
            what = f'{key}/{method}' if method else key
            if ev.mfa_policy:
                self_ = ((settings.get(key) or {}).get('enroll') or {}).get('self')
                rows.append(_chk(f'{tag}{what}: MFA_ENROLL policy allows', 'enroll.self != NOT_ALLOWED', self_ or 'missing from policy', self_ not in (None, 'NOT_ALLOWED'), f'policy "{ev.mfa_policy.get("name")}"'))
            else:
                rows.append(_chk(f'{tag}{what}: MFA_ENROLL policy allows', 'enroll.self != NOT_ALLOWED', None, None, 'no MFA_ENROLL rule among the event targets'))
            auth = (auths or {}).get(key)
            rows.append(_chk(f'{tag}{what}: authenticator ACTIVE org-wide', 'ACTIVE', auth.get('status') if auth else None, (auth.get('status') == 'ACTIVE') if auth else None, err_a))
            if auth and method:
                ms, err_m = _try(ev.lk.methods, auth['id'])
                m = (ms or {}).get(method)
                rows.append(_chk(f'{tag}{what}: method ACTIVE org-wide', 'ACTIVE', m.get('status') if m else None, (m.get('status') == 'ACTIVE') if m else None, err_m or (None if m else 'method not listed')))
            mine = [e for e in enrolls or [] if e.get('key') == key]
            active = [e for e in mine if e.get('status') == 'ACTIVE']
            if err_e:
                rows.append(_chk(f'{tag}{what}: user enrolled', 'ACTIVE enrollment', None, None, err_e))
            else:
                late = bool(active) and all(_ts(e.get('created')) and ev.t and _ts(e['created']) > ev.t for e in active)
                rows.append(_chk(f'{tag}{what}: user enrolled at event time', 'ACTIVE enrollment before the event', [e.get('status') for e in mine] or 'none', bool(active) and not late, 'enrolled only after the event' if late else None))
        if any(r['pass'] is False for r in rows[start:]):
            continue  # already blocked; verified properties can't change the outcome
        missing = []
        for key, _ in methods or [(None, None)]:
            got = _verified_props(ev, key)
            if got is None:
                missing.append(key)
                continue
            for field in props:
                want = _PROPS[field]
                rows.append(_chk(f'{tag}verified property {want}' + (f' ({key})' if key else ''), 'REQUIRED', sorted(got), want in got))
        if missing and props:
            rows.append(_chk(
                f'{tag}verified properties', [_PROPS[f] for f in props], None, None,
                f'no user.authentication.verify event found before the DENY for {", ".join(k or "any authenticator" for k in missing)}',
            ))
    return rows


# ---------------------------------------------------------------------------
# Per-rule and per-denial diagnosis
# ---------------------------------------------------------------------------

def _access(rule):
    a = rule.get('actions') or {}
    return (a.get('appSignOn') or {}).get('access') or (a.get('signon') or {}).get('access')


def _tag(rows, policy, rule):
    return [{'policy': policy.get('name'), 'rule': rule.get('name'), **r} for r in rows]


def _status(rows):
    if any(r['pass'] is False for r in rows):
        return 'blocked'
    return 'undetermined' if any(r['pass'] is None for r in rows) else 'would_allow'


def _diagnose_rule(policy, rules, rule, ev):
    """Explain one Rule target of a DENY. `rules` is the policy's rule list in priority order."""
    ptype, access = policy.get('type'), _access(rule)
    out = {'policy': {'id': policy['id'], 'name': policy.get('name'), 'type': ptype}, 'matched_rule': {
        'id': rule['id'], 'name': rule.get('name'), 'priority': rule.get('priority'), 'access': access}}
    catch_all = access == 'DENY' and not rule.get('conditions')
    if ptype == 'MFA_ENROLL':
        del out['matched_rule']['access']
        out |= {
            'kind': 'enrollment_policy_context',
            'note': 'MFA_ENROLL policy that supplied the enroll settings; not itself a cause of the DENY unless a check below is not true',
            'checks': _tag([r for r in _conditions(rule.get('conditions'), ev) if r['pass'] is not True], policy, rule),
        }
        return out
    if ptype == 'OKTA_SIGN_ON' or (access == 'DENY' and not catch_all):
        out['kind'] = 'explicit_deny_rule' if access == 'DENY' else 'allow_rule_matched'
        out['checks'] = _tag(_conditions(rule.get('conditions'), ev), policy, rule)
        return out
    if catch_all:
        candidates = [r for r in rules if r.get('status') == 'ACTIVE' and (r.get('priority') or 0) < (rule.get('priority') or 0) and _access(r) == 'ALLOW']
    else:
        candidates = [rule]
    out['candidates'] = []
    for c in candidates:
        rows = _tag(_conditions(c.get('conditions'), ev) + _gate(c, ev), policy, c)
        out['candidates'].append({
            'rule': {'id': c['id'], 'name': c.get('name'), 'priority': c.get('priority')}, 'status': _status(rows),
            'blocking': [{k: r[k] for k in ('check', 'required', 'actual')} for r in rows if r['pass'] is False],
            'unresolved': sum(r['pass'] is None for r in rows),
            'checks': rows,
        })
    states = [c['status'] for c in out['candidates']]
    if not catch_all:
        out['kind'] = 'allow_rule_gate_failed' if states[0] == 'blocked' else 'allow_rule_unexplained'
    elif not states:
        out['kind'] = 'no_allow_rule_above_catch_all'
    elif 'would_allow' in states:
        out['kind'] = 'allow_rule_unexplained'
    elif 'undetermined' in states:
        out['kind'] = 'undetermined'
    else:
        out['kind'] = 'no_allow_rule_matched'
    out['candidates'].sort(key=lambda c: (len(c['blocking']), c['unresolved']))
    if out['kind'] in ('no_allow_rule_matched', 'allow_rule_gate_failed'):
        best = out['candidates'][0]
        out['reason'] = f'ALLOW rule "{best["rule"]["name"]}" did not match: ' + '; '.join(
            f'{b["check"]} (required {b["required"]}, actual {b["actual"]})' for b in best['blocking'])
    return out


def _event_summary(e):
    app = next((t for t in e.get('target') or [] if t.get('type') == 'AppInstance'), {})
    return {
        'uuid': e.get('uuid'), 'published': e.get('published'), 'eventType': e.get('eventType'),
        'reason': _get_path(e, 'outcome.reason'), 'app': {'id': app.get('id'), 'name': app.get('displayName')} if app else None,
        'ip': _get_path(e, 'client.ipAddress'), 'zone': _get_path(e, 'client.zone'),
        'isProxy': _get_path(e, 'securityContext.isProxy'), 'rootSessionId': _get_path(e, 'authenticationContext.rootSessionId'),
        'transactionId': _get_path(e, 'transaction.id'), 'device': e.get('device'),
    }


def _signature(e):
    targets = e.get('target') or []
    return (tuple(sorted(t['id'] for t in targets if t.get('type') == 'Rule')),
            next((t.get('id') for t in targets if t.get('type') == 'AppInstance'), None))


def _query(session, base_url, filt, since, until=None, order='DESCENDING', limit=1000):
    params = {'filter': filt, 'since': since, 'sortOrder': order}
    if until:
        params['until'] = until
    params['limit'] = min(limit, 1000)
    return paginated_get(session, '{base}/api/v1/logs', params, limit=limit, path_params={'base': base_url})


def _groups_at(current, changes, t):
    """Undo membership changes published after `t` to recover the user's groups as of the event."""
    groups = set(current)
    for e in changes:  # newest first
        if _ts(e['published']) <= t:
            break
        for tg in e.get('target') or []:
            if 'Group' in (tg.get('type') or ''):
                (groups.discard if e['eventType'].endswith('.add') else groups.add)(tg['id'])
    return groups


def _diagnose_denial(group, ctx):
    event = group['event']
    lk, user, t = ctx['lk'], ctx['user'], _ts(event['published'])
    login = _quote(ctx['login'], '--user')
    ug, err_g = _try(lambda: _groups_at(lk.user_groups(user['id']), ctx['membership'], t))
    verify = _query(ctx['session'], ctx['base'], f'eventType eq "user.authentication.verify" and actor.alternateId eq "{login}"',
                    (t - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%SZ'), event['published'])
    sid = _get_path(event, 'authenticationContext.rootSessionId')
    verify = [e for e in verify if _get_path(e, 'authenticationContext.rootSessionId') == sid] or verify if sid else verify

    resolved, unresolved = [], []
    for tg in (x for x in event.get('target') or [] if x.get('type') == 'Rule'):
        d = tg.get('detailEntry') or {}
        if d.get('policyId'):
            policy, err = _try(lk.policy, d['policyId'])
            rules, err2 = _try(lk.rules, d['policyId'])
            found = (policy, rules, next((r for r in rules or [] if r['id'] == tg['id']), None)) if policy and rules else None
            err = err or err2
        else:
            found, err = lk.find_rule(tg['id'], d.get('policyName')), None
        if found and found[2]:
            resolved.append(found)
        else:
            unresolved.append({'rule_id': tg['id'], 'policy_name': d.get('policyName'), 'error': err or 'rule not found in any policy'})
    mfa = next((p for p, _, r in resolved if p.get('type') == 'MFA_ENROLL'), None)
    ev = _Ev(event, lk, user, ug, verify, mfa)
    diagnoses = [_diagnose_rule(p, rules, r, ev) for p, rules, r in resolved]

    changed = []
    for p, rules, _ in resolved:
        for kind, obj in [('policy', p), *(('rule', x) for x in rules)]:
            if _ts(obj.get('lastUpdated')) and _ts(obj['lastUpdated']) > t:
                changed.append({'type': kind, 'id': obj['id'], 'name': obj.get('name'), 'lastUpdated': obj['lastUpdated']})
    ids = {x['id'] for p, rules, _ in resolved for x in (p, *rules)}
    policy_events = [{'published': e['published'], 'eventType': e['eventType'], 'actor': _get_path(e, 'actor.alternateId'),
                      'targets': [x.get('id') for x in e.get('target') or []]}
                     for e in ctx['policy_changes'] if _ts(e['published']) > t and ids & {x.get('id') for x in e.get('target') or []}]
    return {
        'signature': {'rule_ids': list(group['sig'][0]), 'app_id': group['sig'][1]},
        'count': group['count'], 'first_seen': group['first'], 'last_seen': group['last'],
        'event': _event_summary(event),
        'targets': [{'type': x.get('type'), 'id': x.get('id'), 'name': x.get('displayName'), 'detail': x.get('detailEntry')}
                    for x in event.get('target') or [] if x.get('type') in ('AppInstance', 'UDDevice')],
        'diagnoses': diagnoses,
        'unresolved_rules': unresolved,
        'user_groups_at_event': sorted(ug) if ug is not None else None,
        'changed_after_event': {
            'config_lastUpdated_after_event': changed,
            'policy_events_since': policy_events,
            'group_membership_events_since': [{'published': e['published'], 'eventType': e['eventType'], 'targets': [x.get('id') for x in e.get('target') or []]}
                                              for e in ctx['membership'] if _ts(e['published']) > t],
            'profile_updates_since': [{'published': e['published'], 'actor': _get_path(e, 'actor.alternateId')}
                                      for e in ctx['profile_changes'] if _ts(e['published']) > t],
        },
        **({'warnings': [f'group membership as of the event could not be reconstructed: {err_g}']} if err_g else {}),
    }


# ---------------------------------------------------------------------------
# Non-policy failures
# ---------------------------------------------------------------------------

def _failures(events, locks, concentration):
    sess = [e for e in events if e.get('eventType') == 'user.session.start']
    mfa = [e for e in events if e.get('eventType') == 'user.authentication.auth_via_mfa']
    ips = Counter(_get_path(e, 'client.ipAddress') for e in events)
    top_ip, top_n = ips.most_common(1)[0] if ips else (None, 0)
    return {
        'total': len(events),
        'by_event_type': dict(Counter(e.get('eventType') for e in events).most_common()),
        'session_start_failure_reasons': dict(Counter(_get_path(e, 'outcome.reason') for e in sess).most_common()),
        'mfa_failure_credential_types': dict(Counter(_get_path(e, 'authenticationContext.credentialType') for e in mfa).most_common()),
        'account_lock_events': len(locks),
        'top_ips': [{'ip': ip, 'count': n} for ip, n in ips.most_common(5)],
        'proxy_events': sum(1 for e in events if _get_path(e, 'securityContext.isProxy')),
        'ip_concentration': {'ip': top_ip, 'share': round(top_n / len(events), 2), 'flagged': len(events) >= 5 and top_n / len(events) >= concentration} if events else None,
    }


def cmd_diagnose_login(session, base_url, args):
    login = _quote(args.user, '--user')
    since = args.since or (datetime.now(UTC) - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
    who = f'(actor.alternateId eq "{login}" or target.alternateId eq "{login}")'
    events = _query(session, base_url, f'{who} and (outcome.result eq "DENY" or outcome.result eq "FAILURE")', since, args.until, limit=args.limit)
    lk = _Lookups(session, base_url, args.concurrency)
    user = lk.user(args.user)

    denials = [e for e in events if e.get('outcome', {}).get('result') == 'DENY' and e.get('eventType') == 'policy.evaluate_sign_on']
    others = [e for e in events if e not in denials]
    groups = {}
    for e in denials:  # newest first
        g = groups.setdefault(_signature(e), {'sig': _signature(e), 'event': e, 'count': 0, 'last': e['published']})
        g['count'] += 1
        g['first'] = e['published']
    chosen = list(groups.values())[:args.max_denials]

    oldest = min((g['first'] for g in chosen), default=None)
    ctx = {'session': session, 'base': base_url, 'lk': lk, 'user': user, 'login': args.user,
           'membership': [], 'policy_changes': [], 'profile_changes': []}
    if oldest:
        uid = _quote(user['id'], 'user id')
        ctx['membership'] = _query(session, base_url, f'eventType sw "group.user_membership." and target.id eq "{uid}"', oldest)
        ctx['profile_changes'] = _query(session, base_url, f'eventType eq "user.account.update_profile" and target.id eq "{uid}"', oldest)
        ctx['policy_changes'] = _query(session, base_url, 'eventType sw "policy.rule." or eventType sw "policy.lifecycle."', oldest)
    locks = _query(session, base_url, f'eventType eq "user.account.lock" and target.alternateId eq "{login}"', since, args.until)

    return {
        'summary': {
            'user': {'id': user['id'], 'login': args.user, 'status': user.get('status'), 'lastLogin': user.get('lastLogin')},
            'since': since, 'until': args.until, 'events_fetched': len(events),
            'truncated': bool(args.limit) and len(events) >= args.limit,
            'policy_denials': len(denials), 'distinct_denials': len(groups),
            'diagnosed_denials': len(chosen), 'other_failures': len(others),
        },
        'denials': [_diagnose_denial(g, ctx) for g in chosen],
        'other_failures': _failures(others, locks, args.ip_concentration),
        'notes': [
            'pass is true/false/null; null means the script could not decide — an agent should resolve those rows (see okta-logs SKILL.md "Diagnosing login failures").',
            'All evaluations use signals recorded on the event; config (policies, zones, assurance) is read as of now — see changed_after_event.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description='Mechanically diagnose a user\'s login failures')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('diagnose', help='Diagnose why a user could not log in (policy DENYs walked rule by rule, other failures summarized)')
    p.add_argument('--user', required=True, help='User login / email')
    p.add_argument('--since', help='Start time in ISO 8601 format (defaults to 24 hours ago)')
    p.add_argument('--until', help='End time in ISO 8601 format')
    p.add_argument('--limit', type=int, default=1000, help='Maximum failure events to fetch (default 1000)')
    p.add_argument('--max-denials', dest='max_denials', type=int, default=3, help='Distinct DENY patterns (same rules + app) to diagnose in depth, newest first (default 3)')
    p.add_argument('--ip-concentration', dest='ip_concentration', type=float, default=0.5, help='Flag failures when one IP accounts for at least this share (default 0.5)')
    add_concurrency(p)
    run(parser, {'diagnose': cmd_diagnose_login})


if __name__ == '__main__':
    main()
