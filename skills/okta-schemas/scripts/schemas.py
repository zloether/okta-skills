#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "PyJWT>=2.0",
#   "cryptography>=41.0",
# ]
# ///
"""Read Okta profile mappings, user/group/app schemas, and user types via the Okta API."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'shared'))
from cli import run  # noqa: E402
from okta_client import get_resource, paginated_get  # noqa: E402


def cmd_list(session, base_url, args):
    params = {}
    if args.source_id:
        params['sourceId'] = args.source_id
    if args.target_id:
        params['targetId'] = args.target_id
    return paginated_get(session, f'{base_url}/api/v1/mappings', params, limit=args.limit)


def cmd_get(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/mappings/{args.id}')


def cmd_get_app_user_schema(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/meta/schemas/apps/{args.app_id}/default')


def cmd_get_group_schema(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/meta/schemas/group/default')


def cmd_list_log_stream_schemas(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/meta/schemas/logStream')


def cmd_get_log_stream_schema(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/meta/schemas/logStream/{args.log_stream_type}')


def cmd_list_linked_objects(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/meta/schemas/user/linkedObjects')


def cmd_get_linked_object(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/meta/schemas/user/linkedObjects/{args.name}')


def cmd_get_user_schema(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/meta/schemas/user/{args.schema_id}')


def cmd_list_user_types(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/meta/types/user')


def cmd_get_user_type(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/meta/types/user/{args.type_id}')


def cmd_list_ui_schemas(session, base_url, args):
    return paginated_get(session, f'{base_url}/api/v1/meta/uischemas')


def cmd_get_ui_schema(session, base_url, args):
    return get_resource(session, f'{base_url}/api/v1/meta/uischemas/{args.id}')


def main():
    parser = argparse.ArgumentParser(
        description='Read Okta profile mappings, schemas, and user types'
    )
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List profile mappings')
    p_list.add_argument('--source-id', help='Filter to mappings whose source.id matches this user type or app instance ID')
    p_list.add_argument('--target-id', help='Filter to mappings whose target.id matches this user type or app instance ID')
    p_list.add_argument('--limit', type=int, help='Maximum number of results')

    p_get = sub.add_parser('get', help='Get a profile mapping by ID')
    p_get.add_argument('id', help='Profile mapping ID')

    p_app_schema = sub.add_parser('get-app-user-schema', help="Get an app's default app user schema")
    p_app_schema.add_argument('app_id', help='Application ID')

    sub.add_parser('get-group-schema', help='Get the default group schema')

    sub.add_parser('list-log-stream-schemas', help='List all log stream schemas')

    p_ls_schema = sub.add_parser('get-log-stream-schema', help='Get the schema for a log stream type')
    p_ls_schema.add_argument('log_stream_type', help='Log stream type, e.g. aws_eventbridge or splunk_cloud_logstreaming')

    sub.add_parser('list-linked-objects', help='List all linked object definitions')

    p_linked_object = sub.add_parser('get-linked-object', help='Get a linked object definition by name')
    p_linked_object.add_argument('name', help="Linked object's primary or associated name")

    p_user_schema = sub.add_parser('get-user-schema', help='Get a user schema')
    p_user_schema.add_argument('schema_id', help="Schema ID, or 'default' for the default user type schema")

    sub.add_parser('list-user-types', help='List all user types')

    p_user_type = sub.add_parser('get-user-type', help='Get a user type by ID')
    p_user_type.add_argument('type_id', help="User type ID, or 'default' for the default user type")

    sub.add_parser('list-ui-schemas', help='List all UI schemas')

    p_ui_schema = sub.add_parser('get-ui-schema', help='Get a UI schema by ID')
    p_ui_schema.add_argument('id', help='UI schema ID')

    run(parser, {
        'list': cmd_list,
        'get': cmd_get,
        'get-app-user-schema': cmd_get_app_user_schema,
        'get-group-schema': cmd_get_group_schema,
        'list-log-stream-schemas': cmd_list_log_stream_schemas,
        'get-log-stream-schema': cmd_get_log_stream_schema,
        'list-linked-objects': cmd_list_linked_objects,
        'get-linked-object': cmd_get_linked_object,
        'get-user-schema': cmd_get_user_schema,
        'list-user-types': cmd_list_user_types,
        'get-user-type': cmd_get_user_type,
        'list-ui-schemas': cmd_list_ui_schemas,
        'get-ui-schema': cmd_get_ui_schema,
    })


if __name__ == '__main__':
    main()
