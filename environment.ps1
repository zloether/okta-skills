# This is a placeholder template. Copy it to a new file before adding any values:
#
#   Copy-Item environment.ps1 environment.local.ps1
#   . .\environment.local.ps1
#
# WARNING: Never commit a file containing real credentials to git.
# The copied file should be added to .gitignore or kept outside the repo.

# Your Okta org URL (required)
$env:OKTA_CLIENT_ORGURL = "https://your-org.okta.com"

# Auth method: "PrivateKey" or "SSWS"
# If unset, PrivateKey is used when client ID + key are present, otherwise SSWS.
# $env:OKTA_CLIENT_AUTHORIZATIONMODE = ""

# --- SSWS (API Token) ---
# $env:OKTA_CLIENT_TOKEN = ""

# --- OAuth 2.0 / PrivateKey ---
# $env:OKTA_CLIENT_CLIENTID = ""
# $env:OKTA_CLIENT_PRIVATEKEY = ""        # PEM string, JWK JSON, or path to key file
# $env:OKTA_CLIENT_SCOPES = ""            # e.g. "okta.users.read okta.groups.read"
# $env:OKTA_CLIENT_TOKEN_CACHE_PATH = ""  # optional: path to cache the access token

# --- Optional ---
# $env:OKTA_CLIENT_USERAGENT = ""
# $env:OKTA_CLIENT_CONNECTIONTIMEOUT = "30"
# $env:OKTA_CLIENT_REQUESTTIMEOUT = "30"
# $env:OKTA_CLIENT_CABUNDLE = ""           # path to a CA bundle file or directory; use when behind a corporate proxy with a custom root CA
