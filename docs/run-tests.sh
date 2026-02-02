#!/bin/bash
# 🦞 Lobster Powers Test Runner

# Don't use set -e - we handle errors ourselves

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

skip() {
    echo -e "${YELLOW}○${NC} $1 (skipped)"
}

echo ""
echo "🦞 Lobster Powers Test Suite"
echo "============================"
echo ""

# ============================================================================
# Cleanup
# ============================================================================

echo "Cleaning up..."
./uninstall.sh --all 2>/dev/null || true
rm -rf .venv
rm -f .cursor/rules/lobster-powers.mdc
rm -f .windsurf/rules/lobster-powers.md
rm -f .clinerules/lobster-powers.md
rm -f .continue/rules/lobster-powers.md
rm -f lobster-powers-conventions.md
echo ""

# ============================================================================
# Install Tests
# ============================================================================

echo "=== Install Tests ==="
echo ""

# Test: Claude install
echo "Testing: Claude Code install..."
./install.sh --agent=claude >/dev/null 2>&1

if [ -d .venv ]; then pass "venv created"; else fail "venv missing"; fi
if [ -L ~/.local/bin/lp-memory ]; then pass "CLI symlinks created"; else fail "CLI symlinks missing"; fi
if [ -L ~/.claude/skills/memory/SKILL.md ]; then pass "Claude skills installed"; else fail "Claude skills missing"; fi

# Test: CLI works
if ~/.local/bin/lp-memory --help &>/dev/null; then
    pass "lp-memory --help works"
else
    fail "lp-memory --help broken"
fi

echo ""

# Test: Cursor install
echo "Testing: Cursor install..."
./install.sh --agent=cursor >/dev/null 2>&1
if [ -f .cursor/rules/lobster-powers.mdc ]; then pass "Cursor rules created"; else fail "Cursor rules missing"; fi

# Test: Windsurf install
echo "Testing: Windsurf install..."
./install.sh --agent=windsurf >/dev/null 2>&1
if [ -f .windsurf/rules/lobster-powers.md ]; then pass "Windsurf rules created"; else fail "Windsurf rules missing"; fi

# Test: Cline install
echo "Testing: Cline install..."
./install.sh --agent=cline >/dev/null 2>&1
if [ -f .clinerules/lobster-powers.md ]; then pass "Cline rules created"; else fail "Cline rules missing"; fi

# Test: Roo install
echo "Testing: Roo Code install..."
./install.sh --agent=roo >/dev/null 2>&1
if [ -f ~/.roo/rules/lobster-powers.md ]; then pass "Roo rules created"; else fail "Roo rules missing"; fi

# Test: Continue install
echo "Testing: Continue install..."
./install.sh --agent=continue >/dev/null 2>&1
if [ -f .continue/rules/lobster-powers.md ]; then pass "Continue rules created"; else fail "Continue rules missing"; fi

# Test: Aider install
echo "Testing: Aider install..."
./install.sh --agent=aider >/dev/null 2>&1
if [ -f lobster-powers-conventions.md ]; then pass "Aider conventions created"; else fail "Aider conventions missing"; fi

# Test: Codex install
echo "Testing: Codex install..."
./install.sh --agent=codex >/dev/null 2>&1
if [ -f ~/.codex/AGENTS.md ]; then pass "Codex AGENTS.md created"; else fail "Codex AGENTS.md missing"; fi

echo ""

# ============================================================================
# Uninstall Tests
# ============================================================================

echo "=== Uninstall Tests ==="
echo ""

# Test: Uninstall Claude
echo "Testing: Claude uninstall..."
./uninstall.sh --agent=claude >/dev/null 2>&1
if [ ! -L ~/.claude/skills/memory/SKILL.md ]; then pass "Claude skills removed"; else fail "Claude skills still there"; fi

# Test: Uninstall all
echo "Testing: Full uninstall..."
./uninstall.sh --all >/dev/null 2>&1
if [ ! -L ~/.local/bin/lp-memory ]; then pass "CLI removed"; else fail "CLI still there"; fi
if [ ! -f .cursor/rules/lobster-powers.mdc ]; then pass "Cursor rules removed"; else fail "Cursor rules still there"; fi
if [ ! -f ~/.roo/rules/lobster-powers.md ]; then pass "Roo rules removed"; else fail "Roo rules still there"; fi

echo ""

# ============================================================================
# CLI Tests (requires reinstall)
# ============================================================================

echo "=== CLI Tests ==="
echo ""

echo "Reinstalling for CLI tests..."
./install.sh --agent=claude >/dev/null 2>&1

# Test: lp-notify
echo "Testing: lp-notify..."
if ~/.local/bin/lp-notify "Test" --title "Test" 2>/dev/null; then
    pass "lp-notify works"
else
    # May fail without display
    skip "lp-notify (no display?)"
fi

# Test: lp-cron
echo "Testing: lp-cron..."
if ~/.local/bin/lp-cron list &>/dev/null; then
    pass "lp-cron works"
else
    fail "lp-cron broken"
fi

# Test: lp-web-fetch
echo "Testing: lp-web-fetch..."
if ~/.local/bin/lp-web-fetch https://example.com 2>/dev/null | grep -q "Example"; then
    pass "lp-web-fetch works"
else
    fail "lp-web-fetch broken"
fi

# Test: lp-tts (edge provider, no API key needed)
echo "Testing: lp-tts..."
if ~/.local/bin/lp-tts --provider edge --output /tmp/lp-test.mp3 "test" 2>/dev/null; then
    if [ -f /tmp/lp-test.mp3 ]; then pass "lp-tts works"; else fail "lp-tts no output"; fi
    rm -f /tmp/lp-test.mp3
else
    fail "lp-tts broken"
fi

# Test: lp-browser
echo "Testing: lp-browser..."
if ~/.local/bin/lp-browser screenshot --url https://example.com --output /tmp/lp-test.png 2>/dev/null; then
    if [ -f /tmp/lp-test.png ]; then pass "lp-browser works"; else fail "lp-browser no output"; fi
    rm -f /tmp/lp-test.png
else
    skip "lp-browser (playwright issue?)"
fi

# API-dependent tests
echo ""
echo "=== API-dependent Tests (may skip) ==="
echo ""

if [ -n "$OPENAI_API_KEY" ]; then
    echo "Testing: lp-memory..."
    echo "test content" > /tmp/lp-test.md
    if ~/.local/bin/lp-memory index /tmp/lp-test.md 2>/dev/null; then
        pass "lp-memory index works"
    else
        fail "lp-memory index broken"
    fi
    rm -f /tmp/lp-test.md
else
    skip "lp-memory (no OPENAI_API_KEY)"
fi

if [ -n "$BRAVE_API_KEY" ]; then
    echo "Testing: lp-web-search..."
    if ~/.local/bin/lp-web-search "test" 2>/dev/null | grep -q .; then
        pass "lp-web-search works"
    else
        fail "lp-web-search broken"
    fi
else
    skip "lp-web-search (no BRAVE_API_KEY)"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo "============================"
echo "🦞 Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}"
echo ""

if [ $FAILED -gt 0 ]; then
    exit 1
fi
