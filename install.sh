#!/bin/bash
# Lobster Powers - Install Script
# Creates isolated venv and symlinks commands globally

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
LOCAL_BIN="$HOME/.local/bin"
CLAUDE_COMMANDS="$HOME/.claude/commands"

echo "🦞 Installing Lobster Powers..."

# Create venv
echo "Creating venv in $VENV_DIR..."
python3 -m venv "$VENV_DIR"

# Install package with all extras
echo "Installing package..."
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -e "$SCRIPT_DIR[all]" -q

# Install playwright browsers
echo "Installing Playwright browsers..."
"$VENV_DIR/bin/playwright" install chromium

# Create ~/.local/bin if needed
mkdir -p "$LOCAL_BIN"

# Symlink all lp-* commands
echo "Creating command symlinks in $LOCAL_BIN..."
for cmd in lp-notify lp-tts lp-memory lp-browser lp-cron lp-image lp-web-fetch lp-web-search; do
    if [ -f "$VENV_DIR/bin/$cmd" ]; then
        ln -sf "$VENV_DIR/bin/$cmd" "$LOCAL_BIN/$cmd"
        echo "  ✓ $cmd"
    fi
done

# Create ~/.claude/commands if needed
mkdir -p "$CLAUDE_COMMANDS"

# Symlink all skills
echo "Creating skill symlinks in $CLAUDE_COMMANDS..."
for skill in "$SCRIPT_DIR/skills/"*.md; do
    if [ -f "$skill" ]; then
        name=$(basename "$skill")
        ln -sf "$skill" "$CLAUDE_COMMANDS/$name"
        echo "  ✓ $name"
    fi
done

echo ""
echo "🦞 Lobster Powers installed!"
echo ""
echo "Commands available:"
echo "  lp-notify, lp-tts, lp-memory, lp-browser,"
echo "  lp-cron, lp-image, lp-web-fetch, lp-web-search"
echo ""
echo "Skills available in ~/.claude/commands/"
echo ""
echo "To uninstall: ./uninstall.sh"
