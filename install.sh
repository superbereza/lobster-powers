#!/bin/bash
# 🦞 Lobster Powers - Multi-Agent Installer
# Installs CLI tools and skills for various AI agents

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
LOCAL_BIN="$HOME/.local/bin"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "🦞 Lobster Powers Installer"
echo ""

# ============================================================================
# Agent Detection
# ============================================================================

detect_agents() {
    DETECTED=""

    # Claude Code / OpenCode
    if [ -d "$HOME/.claude" ]; then
        DETECTED="$DETECTED claude"
    fi

    # Codex
    if [ -d "$HOME/.codex" ] || command -v codex &>/dev/null; then
        DETECTED="$DETECTED codex"
    fi

    # Cursor (check for .cursor in common project locations)
    if [ -d "$HOME/.cursor" ] || [ -d ".cursor" ]; then
        DETECTED="$DETECTED cursor"
    fi

    # Windsurf
    if [ -d "$HOME/.windsurf" ] || [ -d ".windsurf" ]; then
        DETECTED="$DETECTED windsurf"
    fi

    # Cline
    if [ -f ".clinerules" ] || [ -d ".clinerules" ] || [ -d ".cline" ]; then
        DETECTED="$DETECTED cline"
    fi

    # Roo Code
    if [ -d "$HOME/.roo" ] || [ -d ".roo" ]; then
        DETECTED="$DETECTED roo"
    fi

    # Continue
    if [ -d "$HOME/.continue" ] || [ -d ".continue" ]; then
        DETECTED="$DETECTED continue"
    fi

    # Aider
    if command -v aider &>/dev/null || [ -f ".aider.conf.yml" ]; then
        DETECTED="$DETECTED aider"
    fi

    echo "$DETECTED"
}

is_detected() {
    echo "$DETECTED_AGENTS" | grep -qw "$1"
}

# ============================================================================
# Installation Functions
# ============================================================================

install_cli() {
    echo "Installing CLI tools..."

    # Create venv if needed
    if [ ! -d "$VENV_DIR" ]; then
        echo "  Creating venv..."
        python3 -m venv "$VENV_DIR"
    fi

    # Install package
    echo "  Installing package..."
    "$VENV_DIR/bin/pip" install --upgrade pip -q
    "$VENV_DIR/bin/pip" install -e "$SCRIPT_DIR[all]" -q

    # Install playwright browsers
    echo "  Installing Playwright browsers..."
    "$VENV_DIR/bin/playwright" install chromium 2>/dev/null || true

    # Check if system deps are missing
    if ! "$VENV_DIR/bin/python" -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); b.close(); p.stop()" 2>/dev/null; then
        echo -e "  ${YELLOW}!${NC} Playwright needs system deps. Run:"
        echo -e "    sudo $VENV_DIR/bin/playwright install-deps chromium"
    fi

    # Create ~/.local/bin if needed
    mkdir -p "$LOCAL_BIN"

    # Symlink commands
    echo "  Creating symlinks in $LOCAL_BIN..."
    for cmd in lp-notify lp-tts lp-memory lp-browser lp-cron lp-image lp-web-fetch lp-web-search; do
        if [ -f "$VENV_DIR/bin/$cmd" ]; then
            ln -sf "$VENV_DIR/bin/$cmd" "$LOCAL_BIN/$cmd"
            echo -e "    ${GREEN}✓${NC} $cmd"
        fi
    done
}

generate_combined_skills() {
    # Concatenate all SKILL.md files with headers
    local output=""
    for skill_dir in "$SCRIPT_DIR/skills/"*/; do
        if [ -d "$skill_dir" ] && [ -f "$skill_dir/SKILL.md" ]; then
            local name=$(basename "$skill_dir")
            output+="
# === $name ===

$(cat "$skill_dir/SKILL.md")

"
        fi
    done
    echo "$output"
}

install_claude() {
    echo "Installing for Claude Code / OpenCode..."
    local skills_root="$HOME/.claude/skills"
    mkdir -p "$skills_root"

    for skill_dir in "$SCRIPT_DIR/skills/"*/; do
        if [ -d "$skill_dir" ] && [ -f "$skill_dir/SKILL.md" ]; then
            local name=$(basename "$skill_dir")
            local target_dir="$skills_root/$name"
            mkdir -p "$target_dir"
            ln -sf "$skill_dir/SKILL.md" "$target_dir/SKILL.md"
            echo -e "  ${GREEN}✓${NC} $name"
        fi
    done
}

install_codex() {
    echo "Installing for Codex..."
    local target="$HOME/.codex/AGENTS.md"
    mkdir -p "$HOME/.codex"

    # Backup existing
    if [ -f "$target" ] && ! grep -q "lobster-powers" "$target" 2>/dev/null; then
        cp "$target" "$target.backup"
        echo -e "  ${YELLOW}!${NC} Backed up existing AGENTS.md"
    fi

    cat > "$target" << 'HEADER'
# Lobster Powers 🦞

OpenClaw superpowers for your AI agent.
CLI tools: lp-memory, lp-browser, lp-tts, lp-cron, lp-notify, lp-image, lp-web-fetch, lp-web-search

HEADER
    generate_combined_skills >> "$target"
    echo -e "  ${GREEN}✓${NC} $target"
}

install_cursor() {
    echo "Installing for Cursor..."
    local target=".cursor/rules/lobster-powers.mdc"
    mkdir -p ".cursor/rules"

    cat > "$target" << 'HEADER'
---
description: Lobster Powers - OpenClaw superpowers for AI agents
globs: ["**/*"]
---

# Lobster Powers 🦞

CLI tools available: lp-memory, lp-browser, lp-tts, lp-cron, lp-notify, lp-image, lp-web-fetch, lp-web-search

HEADER
    generate_combined_skills >> "$target"
    echo -e "  ${GREEN}✓${NC} $target"
}

install_windsurf() {
    echo "Installing for Windsurf..."
    local target=".windsurf/rules/lobster-powers.md"
    mkdir -p ".windsurf/rules"

    cat > "$target" << 'HEADER'
# Lobster Powers 🦞

OpenClaw superpowers for your AI agent.
CLI tools: lp-memory, lp-browser, lp-tts, lp-cron, lp-notify, lp-image, lp-web-fetch, lp-web-search

HEADER
    generate_combined_skills >> "$target"
    echo -e "  ${GREEN}✓${NC} $target"
}

install_cline() {
    echo "Installing for Cline..."
    local target=".clinerules/lobster-powers.md"
    mkdir -p ".clinerules"

    cat > "$target" << 'HEADER'
# Lobster Powers 🦞

OpenClaw superpowers for your AI agent.
CLI tools: lp-memory, lp-browser, lp-tts, lp-cron, lp-notify, lp-image, lp-web-fetch, lp-web-search

HEADER
    generate_combined_skills >> "$target"
    echo -e "  ${GREEN}✓${NC} $target"
}

install_roo() {
    echo "Installing for Roo Code..."
    local target="$HOME/.roo/rules/lobster-powers.md"
    mkdir -p "$HOME/.roo/rules"

    cat > "$target" << 'HEADER'
# Lobster Powers 🦞

OpenClaw superpowers for your AI agent.
CLI tools: lp-memory, lp-browser, lp-tts, lp-cron, lp-notify, lp-image, lp-web-fetch, lp-web-search

HEADER
    generate_combined_skills >> "$target"
    echo -e "  ${GREEN}✓${NC} $target"
}

install_continue() {
    echo "Installing for Continue..."
    local target=".continue/rules/lobster-powers.md"
    mkdir -p ".continue/rules"

    cat > "$target" << 'HEADER'
---
name: lobster-powers
description: OpenClaw superpowers - memory, browser, TTS, cron, and more
---

# Lobster Powers 🦞

CLI tools: lp-memory, lp-browser, lp-tts, lp-cron, lp-notify, lp-image, lp-web-fetch, lp-web-search

HEADER
    generate_combined_skills >> "$target"
    echo -e "  ${GREEN}✓${NC} $target"
}

install_aider() {
    echo "Installing for Aider..."
    local target="lobster-powers-conventions.md"

    cat > "$target" << 'HEADER'
# Lobster Powers 🦞

OpenClaw superpowers for your AI agent.
CLI tools: lp-memory, lp-browser, lp-tts, lp-cron, lp-notify, lp-image, lp-web-fetch, lp-web-search

Use these tools when appropriate for the task.

HEADER
    generate_combined_skills >> "$target"
    echo -e "  ${GREEN}✓${NC} $target"
    echo -e "  ${YELLOW}!${NC} Run aider with: aider --read $target"
}

# ============================================================================
# Menu
# ============================================================================

show_menu() {
    echo "Detected agents:"

    if is_detected "claude"; then
        echo -e "  ${GREEN}✓${NC} Claude Code / OpenCode"
    else
        echo -e "  ${RED}✗${NC} Claude Code / OpenCode"
    fi

    if is_detected "codex"; then
        echo -e "  ${GREEN}✓${NC} Codex"
    else
        echo -e "  ${RED}✗${NC} Codex"
    fi

    if is_detected "cursor"; then
        echo -e "  ${GREEN}✓${NC} Cursor"
    else
        echo -e "  ${RED}✗${NC} Cursor"
    fi

    if is_detected "windsurf"; then
        echo -e "  ${GREEN}✓${NC} Windsurf"
    else
        echo -e "  ${RED}✗${NC} Windsurf"
    fi

    if is_detected "cline"; then
        echo -e "  ${GREEN}✓${NC} Cline"
    else
        echo -e "  ${RED}✗${NC} Cline"
    fi

    if is_detected "roo"; then
        echo -e "  ${GREEN}✓${NC} Roo Code"
    else
        echo -e "  ${RED}✗${NC} Roo Code"
    fi

    if is_detected "continue"; then
        echo -e "  ${GREEN}✓${NC} Continue"
    else
        echo -e "  ${RED}✗${NC} Continue"
    fi

    if is_detected "aider"; then
        echo -e "  ${GREEN}✓${NC} Aider"
    else
        echo -e "  ${RED}✗${NC} Aider"
    fi

    echo ""
    echo "Install for:"
    echo "  1) Claude Code / OpenCode"
    echo "  2) Codex"
    echo "  3) Cursor"
    echo "  4) Windsurf"
    echo "  5) Cline"
    echo "  6) Roo Code"
    echo "  7) Continue"
    echo "  8) Aider"
    echo "  9) All detected"
    echo "  0) CLI only (no skills)"
    echo ""
}

# ============================================================================
# Main
# ============================================================================

DETECTED_AGENTS=$(detect_agents)

# Parse arguments
AGENT=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --agent=*)
            AGENT="${1#*=}"
            shift
            ;;
        --help|-h)
            echo "Usage: ./install.sh [--agent=NAME]"
            echo ""
            echo "Agents: claude, codex, cursor, windsurf, cline, roo, continue, aider, all"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# Non-interactive mode
if [ -n "$AGENT" ]; then
    install_cli
    echo ""

    case $AGENT in
        claude)   install_claude ;;
        codex)    install_codex ;;
        cursor)   install_cursor ;;
        windsurf) install_windsurf ;;
        cline)    install_cline ;;
        roo)      install_roo ;;
        continue) install_continue ;;
        aider)    install_aider ;;
        all)
            [ -n "$DETECTED_AGENTS" ] || { echo "No agents detected"; exit 1; }
            is_detected "claude" && install_claude
            is_detected "codex" && install_codex
            is_detected "cursor" && install_cursor
            is_detected "windsurf" && install_windsurf
            is_detected "cline" && install_cline
            is_detected "roo" && install_roo
            is_detected "continue" && install_continue
            is_detected "aider" && install_aider
            ;;
        *)
            echo "Unknown agent: $AGENT"
            exit 1
            ;;
    esac
else
    # Interactive mode
    show_menu
    read -p "Choice [1]: " choice
    choice=${choice:-1}

    install_cli
    echo ""

    case $choice in
        1) install_claude ;;
        2) install_codex ;;
        3) install_cursor ;;
        4) install_windsurf ;;
        5) install_cline ;;
        6) install_roo ;;
        7) install_continue ;;
        8) install_aider ;;
        9)
            is_detected "claude" && install_claude
            is_detected "codex" && install_codex
            is_detected "cursor" && install_cursor
            is_detected "windsurf" && install_windsurf
            is_detected "cline" && install_cline
            is_detected "roo" && install_roo
            is_detected "continue" && install_continue
            is_detected "aider" && install_aider
            ;;
        0) echo "CLI only - no skills installed" ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac
fi

echo ""
echo "🦞 Lobster Powers installed!"
echo ""
echo "CLI commands: lp-notify, lp-tts, lp-memory, lp-browser, lp-cron, lp-image, lp-web-fetch, lp-web-search"
echo ""

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}⚠️  ~/.local/bin is not in your PATH${NC}"
    echo ""
    echo "Add this to your ~/.bashrc or ~/.zshrc:"
    echo ""
    echo '  export PATH="$HOME/.local/bin:$PATH"'
    echo ""
    echo "Then run: source ~/.bashrc (or restart terminal)"
    echo ""
fi

echo "To uninstall: ./uninstall.sh"
