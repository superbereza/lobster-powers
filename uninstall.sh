#!/bin/bash
# Lobster Powers - Uninstall Script
# Removes venv and all symlinks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
LOCAL_BIN="$HOME/.local/bin"
CLAUDE_COMMANDS="$HOME/.claude/commands"

echo "🦞 Uninstalling Lobster Powers..."

# Remove command symlinks
echo "Removing command symlinks..."
for cmd in lp-notify lp-tts lp-memory lp-browser lp-cron lp-image lp-web-fetch lp-web-search; do
    if [ -L "$LOCAL_BIN/$cmd" ]; then
        rm "$LOCAL_BIN/$cmd"
        echo "  ✓ Removed $cmd"
    fi
done

# Remove skill symlinks
echo "Removing skill symlinks..."
for skill in browser cron image memory notify tts web-fetch web-search; do
    if [ -L "$CLAUDE_COMMANDS/$skill.md" ]; then
        rm "$CLAUDE_COMMANDS/$skill.md"
        echo "  ✓ Removed $skill.md"
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
