#!/usr/bin/env bash
set -euo pipefail

SPEC_URL="https://raw.githubusercontent.com/okta/okta-management-openapi-spec/refs/heads/master/dist/current/management-minimal.yaml"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

curl -fsSL "$SPEC_URL" -o "$REPO_ROOT/management-minimal.yaml"
