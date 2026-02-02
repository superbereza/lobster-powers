#!/bin/bash
# Lobster Powers - Install Script
# Creates isolated venv and symlinks commands globally

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
LOCAL_BIN="$HOME/.local/bin"
# Skills go to parent dir so all sibling projects auto-discover them
SKILLS_ROOT="$(dirname "$SCRIPT_DIR")/.claude/skills"

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

# Symlink all skills to parent .claude/skills/ for auto-discovery
echo "Creating skill symlinks in $SKILLS_ROOT..."
for skill in "$SCRIPT_DIR/skills/"*.md; do
    if [ -f "$skill" ]; then
        # browser.md -> lp-browser/SKILL.md
        name=$(basename "$skill" .md)
        skill_dir="$SKILLS_ROOT/lp-$name"
        mkdir -p "$skill_dir"
        ln -sf "$skill" "$skill_dir/SKILL.md"
        echo "  ✓ lp-$name"
    fi
done

echo ""
echo "🦞 Lobster Powers installed!"
echo ""
echo "Commands available:"
echo "  lp-notify, lp-tts, lp-memory, lp-browser,"
echo "  lp-cron, lp-image, lp-web-fetch, lp-web-search"
echo ""
echo "Skills installed to: $SKILLS_ROOT"
echo "(Auto-discovered by Claude in all sibling projects)"
echo ""
echo "To uninstall: ./uninstall.sh"
