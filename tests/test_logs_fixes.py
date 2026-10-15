import json
from unittest.mock import MagicMock

from conftest import args, make_response
from test_scripts import import_script

BASE_URL = 'https://example.okta.com'
logs = import_script('okta-logs', 'logs.py')


def _a(**kw):
    d = {'since': None, 'until': None, 'filter': None, 'q': None, 'sort_order': None, 'limit': None, 'jsonl': False,
             'count_by': None, 'member_of': None, 'select': None, 'strip_links': False, 'page_size': None,
             'user': None, 'app': None}
    d.update(kw)
    return args(**d)


def _params(session):
    return session.get.call_args[1]['params']


def _events(n):
    return [{'eventType': 'x', 'outcome': {'result': 'SUCCESS'}} for _ in range(n)]


def test_list_without_limit_sends_no_limit():
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_list(session, BASE_URL, _a())
    assert 'limit' not in _params(session)


def test_list_limit_one_requests_one_event():
    session = MagicMock()
    session.get.return_value = make_response(_events(1))
    result = logs.cmd_list(session, BASE_URL, _a(limit=1))
    assert _params(session)['limit'] == 1
    assert len(result) == 1


def test_list_limit_capped_at_1000():
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_list(session, BASE_URL, _a(limit=5000))
    assert _params(session)['limit'] == 1000


def test_list_page_size_with_count_by_still_counts_all_pages():
    session = MagicMock()
    session.get.side_effect = [
        make_response(_events(2), next_url=f'{BASE_URL}/api/v1/logs?after=1'),
        make_response(_events(1)),
    ]
    result = logs.cmd_list(session, BASE_URL, _a(page_size=2, count_by='outcome.result'))
    assert session.get.call_args_list[0][1]['params']['limit'] == 2
    assert result['total'] == 3


def test_jsonl_limit_slicing_still_honored_with_page_size(capsys):
    session = MagicMock()
    session.get.side_effect = [
        make_response(_events(2), next_url=f'{BASE_URL}/api/v1/logs?after=1'),
        make_response(_events(2)),
    ]
    logs.cmd_list(session, BASE_URL, _a(jsonl=True, limit=3, page_size=2))
    assert len(capsys.readouterr().out.strip().splitlines()) == 3


def test_member_of_quotes_group_id_in_path():
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_list(session, BASE_URL, _a(member_of='apps/x?y#z'))
    assert session.get.call_args_list[0][0][0] == f'{BASE_URL}/api/v1/groups/apps%2Fx%3Fy%23z/users'


def test_timeline_limit_sent():
    session = MagicMock()
    session.get.return_value = make_response(_events(1))
    rows = logs.cmd_timeline(session, BASE_URL, _a(limit=1))
    assert _params(session)['limit'] == 1
    assert len(rows) == 1


def test_login_failures_limit_sent_and_without_limit_not_sent():
    session = MagicMock()
    session.get.return_value = make_response(_events(1))
    logs.cmd_login_failures(session, BASE_URL, _a(limit=1))
    assert _params(session)['limit'] == 1
    logs.cmd_login_failures(session, BASE_URL, _a())
    assert 'limit' not in _params(session)


def test_timeline_passes_since_until_through():
    session = MagicMock()
    session.get.return_value = make_response([])
    logs.cmd_timeline(session, BASE_URL, _a(since='2026-01-01T00:00:00Z', until='2026-01-02T00:00:00Z'))
    assert _params(session)['since'] == '2026-01-01T00:00:00Z'
    assert _params(session)['until'] == '2026-01-02T00:00:00Z'


def test_timeline_jsonl_streams_reshaped_rows(capsys):
    session = MagicMock()
    session.get.return_value = make_response(_events(2))
    result = logs.cmd_timeline(session, BASE_URL, _a(jsonl=True))
    assert result is logs.STREAMED
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])['eventType'] == 'x'
