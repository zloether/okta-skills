#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS="$REPO/skills"

usage() {
    cat <<EOF
Usage: $(basename "$0") [--global] [--local [PATH]]

  --global          Install into global AI agent skill directories
  --local [PATH]    Install into project-level skill directories
                    (defaults to current directory if PATH is omitted)

Both flags can be combined.
EOF
    exit 1
}

INSTALL_GLOBAL=false
LOCAL_PATH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --global)
            INSTALL_GLOBAL=true
            shift
            ;;
        --local)
            shift
            if [[ $# -gt 0 && "$1" != --* ]]; then
                # Resolve to absolute path without requiring the directory to exist
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
        -h|--help) usage ;;
        *) echo "error: unknown option: $1" >&2; usage ;;
    esac
done

if ! $INSTALL_GLOBAL && [[ -z "$LOCAL_PATH" ]]; then
    usage
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
            ln -sf "$skill" "$link"
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
    link_skills "$HOME/.claude/skills"                "claude (global)"
    link_skills "$HOME/.codeium/windsurf/skills"      "windsurf (global)"
    link_skills "$HOME/.copilot/skills"               "copilot (global)"
    link_skills "$HOME/.gemini/skills"                "gemini (global)"
    echo "cursor — no global skills directory"
    echo ""
fi

if [[ -n "$LOCAL_PATH" ]]; then
    link_skills "$LOCAL_PATH/.claude/skills"   "claude (local)"
    link_skills "$LOCAL_PATH/.cursor/skills"   "cursor (local)"
    link_skills "$LOCAL_PATH/.windsurf/skills" "windsurf (local)"
    link_skills "$LOCAL_PATH/.github/skills"   "copilot (local)"
    link_skills "$LOCAL_PATH/.gemini/skills"   "gemini (local)"
    echo ""
fi

echo "Done."
