#!/bin/bash
# Lobster Powers - Uninstall Script
# Removes venv and all symlinks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
LOCAL_BIN="$HOME/.local/bin"
SKILLS_ROOT="$HOME/.claude/skills"

echo "🦞 Uninstalling Lobster Powers..."

# Remove command symlinks
echo "Removing command symlinks..."
for cmd in lp-notify lp-tts lp-memory lp-browser lp-cron lp-image lp-web-fetch lp-web-search; do
    if [ -L "$LOCAL_BIN/$cmd" ]; then
        rm "$LOCAL_BIN/$cmd"
        echo "  ✓ Removed $cmd"
    fi
done

# Remove skill directories
echo "Removing skills from $SKILLS_ROOT..."
for skill in browser cron image memory notify tts web-fetch web-search; do
    skill_dir="$SKILLS_ROOT/lp-$skill"
    if [ -d "$skill_dir" ]; then
        rm -rf "$skill_dir"
        echo "  ✓ Removed lp-$skill"
    fi
done

# Remove venv
if [ -d "$VENV_DIR" ]; then
    echo "Removing venv..."
    rm -rf "$VENV_DIR"
    echo "  ✓ Removed .venv"
fi

echo ""
echo "🦞 Lobster Powers uninstalled!"
