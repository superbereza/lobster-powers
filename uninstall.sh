#!/bin/bash
# 🦞 Lobster Powers - Multi-Agent Uninstaller
# Removes CLI tools and skills for various AI agents

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
LOCAL_BIN="$HOME/.local/bin"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "🦞 Lobster Powers Uninstaller"
echo ""

# ============================================================================
# Detection Functions
# ============================================================================

detect_installed() {
    INSTALLED=""

    # Claude Code / OpenCode
    if [ -L "$HOME/.claude/skills/browser/SKILL.md" ] || [ -L "$HOME/.claude/skills/memory/SKILL.md" ]; then
        INSTALLED="$INSTALLED claude"
    fi

    # Codex
    if [ -f "$HOME/.codex/AGENTS.md" ] && grep -q "Lobster Powers" "$HOME/.codex/AGENTS.md" 2>/dev/null; then
        INSTALLED="$INSTALLED codex"
    fi

    # Cursor
    if [ -f ".cursor/rules/lobster-powers.mdc" ]; then
        INSTALLED="$INSTALLED cursor"
    fi

    # Windsurf
    if [ -f ".windsurf/rules/lobster-powers.md" ]; then
        INSTALLED="$INSTALLED windsurf"
    fi

    # Cline
    if [ -f ".clinerules/lobster-powers.md" ]; then
        INSTALLED="$INSTALLED cline"
    fi

    # Roo Code
    if [ -f "$HOME/.roo/rules/lobster-powers.md" ]; then
        INSTALLED="$INSTALLED roo"
    fi

    # Continue
    if [ -f ".continue/rules/lobster-powers.md" ]; then
        INSTALLED="$INSTALLED continue"
    fi

    # Aider
    if [ -f "lobster-powers-conventions.md" ]; then
        INSTALLED="$INSTALLED aider"
    fi

    # CLI
    if [ -L "$LOCAL_BIN/lp-memory" ]; then
        INSTALLED="$INSTALLED cli"
    fi

    echo "$INSTALLED"
}

is_installed() {
    echo "$INSTALLED_AGENTS" | grep -qw "$1"
}

# ============================================================================
# Uninstall Functions
# ============================================================================

uninstall_cli() {
    echo "Removing CLI tools..."

    for cmd in lp-notify lp-tts lp-memory lp-browser lp-cron lp-image lp-web-fetch lp-web-search; do
        if [ -L "$LOCAL_BIN/$cmd" ]; then
            rm "$LOCAL_BIN/$cmd"
            echo -e "  ${GREEN}✓${NC} Removed $cmd"
        fi
    done

    if [ -d "$VENV_DIR" ]; then
        echo "  Removing venv..."
        rm -rf "$VENV_DIR"
        echo -e "  ${GREEN}✓${NC} Removed .venv"
    fi
}

uninstall_claude() {
    echo "Removing from Claude Code / OpenCode..."
    local skills_root="$HOME/.claude/skills"

    for skill in browser cron image memory notify tts web-fetch web-search; do
        if [ -d "$skills_root/$skill" ]; then
            rm -rf "$skills_root/$skill"
            echo -e "  ${GREEN}✓${NC} Removed $skill"
        fi
    done
}

uninstall_codex() {
    echo "Removing from Codex..."
    local target="$HOME/.codex/AGENTS.md"

    if [ -f "$target" ]; then
        rm "$target"
        echo -e "  ${GREEN}✓${NC} Removed $target"

        # Restore backup if exists
        if [ -f "$target.backup" ]; then
            mv "$target.backup" "$target"
            echo -e "  ${YELLOW}!${NC} Restored backup AGENTS.md"
        fi
    fi
}

uninstall_cursor() {
    echo "Removing from Cursor..."
    local target=".cursor/rules/lobster-powers.mdc"

    if [ -f "$target" ]; then
        rm "$target"
        echo -e "  ${GREEN}✓${NC} Removed $target"
    fi
}

uninstall_windsurf() {
    echo "Removing from Windsurf..."
    local target=".windsurf/rules/lobster-powers.md"

    if [ -f "$target" ]; then
        rm "$target"
        echo -e "  ${GREEN}✓${NC} Removed $target"
    fi
}

uninstall_cline() {
    echo "Removing from Cline..."
    local target=".clinerules/lobster-powers.md"

    if [ -f "$target" ]; then
        rm "$target"
        echo -e "  ${GREEN}✓${NC} Removed $target"
    fi
}

uninstall_roo() {
    echo "Removing from Roo Code..."
    local target="$HOME/.roo/rules/lobster-powers.md"

    if [ -f "$target" ]; then
        rm "$target"
        echo -e "  ${GREEN}✓${NC} Removed $target"
    fi
}

uninstall_continue() {
    echo "Removing from Continue..."
    local target=".continue/rules/lobster-powers.md"

    if [ -f "$target" ]; then
        rm "$target"
        echo -e "  ${GREEN}✓${NC} Removed $target"
    fi
}

uninstall_aider() {
    echo "Removing from Aider..."
    local target="lobster-powers-conventions.md"

    if [ -f "$target" ]; then
        rm "$target"
        echo -e "  ${GREEN}✓${NC} Removed $target"
    fi
}

# ============================================================================
# Menu
# ============================================================================

show_menu() {
    echo "Installed components:"

    if is_installed "cli"; then
        echo -e "  ${GREEN}✓${NC} CLI tools"
    fi

    if is_installed "claude"; then
        echo -e "  ${GREEN}✓${NC} Claude Code / OpenCode"
    fi

    if is_installed "codex"; then
        echo -e "  ${GREEN}✓${NC} Codex"
    fi

    if is_installed "cursor"; then
        echo -e "  ${GREEN}✓${NC} Cursor"
    fi

    if is_installed "windsurf"; then
        echo -e "  ${GREEN}✓${NC} Windsurf"
    fi

    if is_installed "cline"; then
        echo -e "  ${GREEN}✓${NC} Cline"
    fi

    if is_installed "roo"; then
        echo -e "  ${GREEN}✓${NC} Roo Code"
    fi

    if is_installed "continue"; then
        echo -e "  ${GREEN}✓${NC} Continue"
    fi

    if is_installed "aider"; then
        echo -e "  ${GREEN}✓${NC} Aider"
    fi

    if [ -z "$INSTALLED_AGENTS" ]; then
        echo -e "  ${YELLOW}Nothing installed${NC}"
        exit 0
    fi

    echo ""
    echo "Uninstall:"
    echo "  1) Claude Code / OpenCode"
    echo "  2) Codex"
    echo "  3) Cursor"
    echo "  4) Windsurf"
    echo "  5) Cline"
    echo "  6) Roo Code"
    echo "  7) Continue"
    echo "  8) Aider"
    echo "  9) All installed"
    echo "  0) CLI only"
    echo ""
}

# ============================================================================
# Main
# ============================================================================

INSTALLED_AGENTS=$(detect_installed)

# Parse arguments
AGENT=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --agent=*)
            AGENT="${1#*=}"
            shift
            ;;
        --all)
            AGENT="all"
            shift
            ;;
        --help|-h)
            echo "Usage: ./uninstall.sh [--agent=NAME] [--all]"
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
    case $AGENT in
        claude)   uninstall_claude ;;
        codex)    uninstall_codex ;;
        cursor)   uninstall_cursor ;;
        windsurf) uninstall_windsurf ;;
        cline)    uninstall_cline ;;
        roo)      uninstall_roo ;;
        continue) uninstall_continue ;;
        aider)    uninstall_aider ;;
        cli)      uninstall_cli ;;
        all)
            is_installed "claude" && uninstall_claude
            is_installed "codex" && uninstall_codex
            is_installed "cursor" && uninstall_cursor
            is_installed "windsurf" && uninstall_windsurf
            is_installed "cline" && uninstall_cline
            is_installed "roo" && uninstall_roo
            is_installed "continue" && uninstall_continue
            is_installed "aider" && uninstall_aider
            is_installed "cli" && uninstall_cli
            ;;
        *)
            echo "Unknown agent: $AGENT"
            exit 1
            ;;
    esac
else
    # Interactive mode
    show_menu
    read -p "Choice [9]: " choice
    choice=${choice:-9}

    case $choice in
        1) uninstall_claude ;;
        2) uninstall_codex ;;
        3) uninstall_cursor ;;
        4) uninstall_windsurf ;;
        5) uninstall_cline ;;
        6) uninstall_roo ;;
        7) uninstall_continue ;;
        8) uninstall_aider ;;
        9)
            is_installed "claude" && uninstall_claude
            is_installed "codex" && uninstall_codex
            is_installed "cursor" && uninstall_cursor
            is_installed "windsurf" && uninstall_windsurf
            is_installed "cline" && uninstall_cline
            is_installed "roo" && uninstall_roo
            is_installed "continue" && uninstall_continue
            is_installed "aider" && uninstall_aider
            is_installed "cli" && uninstall_cli
            ;;
        0) uninstall_cli ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac
fi

echo ""
echo "🦞 Lobster Powers uninstalled!"
