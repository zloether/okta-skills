#!/usr/bin/env bash
# This is a placeholder template. Copy it to a new file before adding any values:
#
#   cp environment.sh environment.local.sh
#   source environment.local.sh
#
# WARNING: Never commit a file containing real credentials to git.
# The copied file should be added to .gitignore or kept outside the repo.

# Your Okta org URL (required)
export OKTA_CLIENT_ORGURL="https://your-org.okta.com"

# Auth method: "PrivateKey" or "SSWS"
# If unset, PrivateKey is used when client ID + key are present, otherwise SSWS.
# export OKTA_CLIENT_AUTHORIZATIONMODE=""

# --- SSWS (API Token) ---
# export OKTA_CLIENT_TOKEN=""

# --- OAuth 2.0 / PrivateKey ---
# export OKTA_CLIENT_CLIENTID=""
# export OKTA_CLIENT_PRIVATEKEY=""        # PEM string, JWK JSON, or path to key file
# export OKTA_CLIENT_SCOPES=""            # e.g. "okta.users.read okta.groups.read"
# export OKTA_CLIENT_TOKEN_CACHE_PATH=""  # optional: path to cache the access token

# --- Optional ---
# export OKTA_CLIENT_USERAGENT=""
# export OKTA_CLIENT_CONNECTIONTIMEOUT="30"
# export OKTA_CLIENT_REQUESTTIMEOUT="30"
# export OKTA_CLIENT_CABUNDLE=""           # path to a CA bundle file or directory; takes precedence over REQUESTS_CA_BUNDLE if both are set
