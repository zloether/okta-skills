#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS="$REPO/skills"

usage() {
    cat <<EOF
Usage: $(basename "$0") [--global] [--local [PATH]] [--claude] [--cursor] [--windsurf] [--copilot] [--gemini]

  --global          Install into global AI agent skill directories
  --local [PATH]    Install into project-level skill directories
                    (defaults to current directory if PATH is omitted)

  --claude          Install for Claude Code only
  --cursor          Install for Cursor only
  --windsurf        Install for Windsurf only
  --copilot         Install for GitHub Copilot only
  --gemini          Install for Gemini only

If no agent flags are provided, all agents are installed.
--global and --local can be combined. Agent flags can be combined.
EOF
    exit 1
}

INSTALL_GLOBAL=false
LOCAL_PATH=""
OPT_CLAUDE=false
OPT_CURSOR=false
OPT_WINDSURF=false
OPT_COPILOT=false
OPT_GEMINI=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --global)   INSTALL_GLOBAL=true; shift ;;
        --local)
            shift
            if [[ $# -gt 0 && "$1" != --* ]]; then
                if [[ "$1" = /* ]]; then
                    LOCAL_PATH="$1"
                else
                    LOCAL_PATH="$(pwd)/$1"
                fi
                shift
            else
                LOCAL_PATH="$(pwd)"
            fi
            ;;
        --claude)   OPT_CLAUDE=true;   shift ;;
        --cursor)   OPT_CURSOR=true;   shift ;;
        --windsurf) OPT_WINDSURF=true; shift ;;
        --copilot)  OPT_COPILOT=true;  shift ;;
        --gemini)   OPT_GEMINI=true;   shift ;;
        -h|--help)  usage ;;
        *) echo "error: unknown option: $1" >&2; usage ;;
    esac
done

if ! $INSTALL_GLOBAL && [[ -z "$LOCAL_PATH" ]]; then
    usage
fi

# Guard: prevent installing into the repo's own skills directory
if [[ -n "$LOCAL_PATH" && ( "$LOCAL_PATH" == "$REPO" || "$LOCAL_PATH" == "$REPO"/* ) ]]; then
    echo "error: --local path cannot be inside the okta-skills repo itself" >&2
    exit 1
fi

# If no agent flags given, enable all
if ! $OPT_CLAUDE && ! $OPT_CURSOR && ! $OPT_WINDSURF && ! $OPT_COPILOT && ! $OPT_GEMINI; then
    OPT_CLAUDE=true
    OPT_CURSOR=true
    OPT_WINDSURF=true
    OPT_COPILOT=true
    OPT_GEMINI=true
fi

link_skills() {
    local dest_dir="$1"
    local label="$2"
    echo "$label"
    echo "  $dest_dir"
    mkdir -p "$dest_dir"
    for skill in "$SKILLS"/*/; do
        local name
        name="$(basename "$skill")"
        local link="$dest_dir/$name"
        if [[ -L "$link" ]]; then
            ln -sfn "$skill" "$link"
            echo "  updated: $name"
        elif [[ -e "$link" ]]; then
            echo "  skipped: $name (exists and is not a symlink)"
        else
            ln -s "$skill" "$link"
            echo "  linked:  $name"
        fi
    done
}

if $INSTALL_GLOBAL; then
    $OPT_CLAUDE   && link_skills "$HOME/.claude/skills"           "claude (global)"
    $OPT_WINDSURF && link_skills "$HOME/.codeium/windsurf/skills" "windsurf (global)"
    $OPT_COPILOT  && link_skills "$HOME/.copilot/skills"          "copilot (global)"
    $OPT_GEMINI   && link_skills "$HOME/.gemini/skills"           "gemini (global)"
    $OPT_CURSOR   && echo "cursor — no global skills directory"
    echo ""
fi

if [[ -n "$LOCAL_PATH" ]]; then
    $OPT_CLAUDE   && link_skills "$LOCAL_PATH/.claude/skills"   "claude (local)"
    $OPT_CURSOR   && link_skills "$LOCAL_PATH/.cursor/skills"   "cursor (local)"
    $OPT_WINDSURF && link_skills "$LOCAL_PATH/.windsurf/skills" "windsurf (local)"
    $OPT_COPILOT  && link_skills "$LOCAL_PATH/.github/skills"   "copilot (local)"
    $OPT_GEMINI   && link_skills "$LOCAL_PATH/.gemini/skills"   "gemini (local)"
    echo ""
fi

# ─── Runtime setup ──────────────────────────────────────────────────────────
echo "Setting up Python runtime..."

if command -v uv &>/dev/null; then
    echo "  uv $(uv --version) — scripts will run via: uv run <script>"
else
    echo "  uv not found (preferred runtime for dependency management)."
    if [[ "$(uname)" == "Darwin" ]] && command -v brew &>/dev/null; then
        echo "  Install with: brew install uv"
    else
        echo "  Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
fi

if [[ ! -d "$REPO/.venv" ]]; then
    if command -v python3 &>/dev/null; then
        echo "  Creating .venv fallback..."
        python3 -m venv "$REPO/.venv"
        "$REPO/.venv/bin/pip" install -q -r "$REPO/requirements.txt"
        echo "  .venv created at $REPO/.venv"
    else
        echo "  python3 not found — skipping .venv creation"
        echo "  Install Python 3.8+ if you are not using uv"
    fi
else
    echo "  .venv already exists at $REPO/.venv"
fi
echo ""

echo "Done."
