# Testing Lobster Powers

## Install Script Tests

### Test 1: Fresh install for Claude Code

```bash
# Clean state
./uninstall.sh --all 2>/dev/null || true
rm -rf .venv

# Install
./install.sh --agent=claude

# Verify
[ -d .venv ] && echo "✓ venv created" || echo "✗ venv missing"
[ -L ~/.local/bin/lp-memory ] && echo "✓ CLI symlinks" || echo "✗ CLI missing"
[ -L ~/.claude/skills/memory/SKILL.md ] && echo "✓ Skills installed" || echo "✗ Skills missing"
lp-memory --help &>/dev/null && echo "✓ CLI works" || echo "✗ CLI broken"
```

### Test 2: Fresh install for Codex

```bash
./uninstall.sh --all 2>/dev/null || true
rm -rf .venv

./install.sh --agent=codex

[ -f ~/.codex/AGENTS.md ] && echo "✓ AGENTS.md created" || echo "✗ AGENTS.md missing"
grep -q "Lobster Powers" ~/.codex/AGENTS.md && echo "✓ Content correct" || echo "✗ Content wrong"
```

### Test 3: Fresh install for Cursor

```bash
./uninstall.sh --all 2>/dev/null || true
rm -rf .venv

./install.sh --agent=cursor

[ -f .cursor/rules/lobster-powers.mdc ] && echo "✓ Cursor rules created" || echo "✗ Rules missing"
grep -q "Lobster Powers" .cursor/rules/lobster-powers.mdc && echo "✓ Content correct" || echo "✗ Content wrong"
```

### Test 4: Fresh install for Windsurf

```bash
./uninstall.sh --all 2>/dev/null || true
rm -rf .venv

./install.sh --agent=windsurf

[ -f .windsurf/rules/lobster-powers.md ] && echo "✓ Windsurf rules created" || echo "✗ Rules missing"
```

### Test 5: Fresh install for Cline

```bash
./uninstall.sh --all 2>/dev/null || true
rm -rf .venv

./install.sh --agent=cline

[ -f .clinerules/lobster-powers.md ] && echo "✓ Cline rules created" || echo "✗ Rules missing"
```

### Test 6: Fresh install for Roo Code

```bash
./uninstall.sh --all 2>/dev/null || true
rm -rf .venv

./install.sh --agent=roo

[ -f ~/.roo/rules/lobster-powers.md ] && echo "✓ Roo rules created" || echo "✗ Rules missing"
```

### Test 7: Fresh install for Continue

```bash
./uninstall.sh --all 2>/dev/null || true
rm -rf .venv

./install.sh --agent=continue

[ -f .continue/rules/lobster-powers.md ] && echo "✓ Continue rules created" || echo "✗ Rules missing"
```

### Test 8: Fresh install for Aider

```bash
./uninstall.sh --all 2>/dev/null || true
rm -rf .venv

./install.sh --agent=aider

[ -f lobster-powers-conventions.md ] && echo "✓ Aider conventions created" || echo "✗ Conventions missing"
```

---

## Uninstall Script Tests

### Test 9: Uninstall Claude

```bash
./install.sh --agent=claude
./uninstall.sh --agent=claude

[ ! -L ~/.claude/skills/memory/SKILL.md ] && echo "✓ Skills removed" || echo "✗ Skills still there"
```

### Test 10: Uninstall all

```bash
./install.sh --agent=claude
./uninstall.sh --all

[ ! -L ~/.local/bin/lp-memory ] && echo "✓ CLI removed" || echo "✗ CLI still there"
[ ! -d .venv ] && echo "✓ venv removed" || echo "✗ venv still there"
```

---

## CLI Tool Tests

### Test 11: lp-notify

```bash
lp-notify "Test notification" --title "Lobster Test"
# Should show desktop notification
```

### Test 12: lp-tts

```bash
lp-tts "Hello, I am a lobster with powers" --provider edge
# Should play audio
```

### Test 13: lp-memory

```bash
# Index a file
echo "Test content for lobster" > /tmp/lobster-test.md
lp-memory index /tmp/lobster-test.md

# Search
lp-memory search "lobster"
# Should find the test file

# Cleanup
rm /tmp/lobster-test.md
```

### Test 14: lp-cron

```bash
lp-cron list
# Should show cron jobs (or empty list)
```

### Test 15: lp-web-fetch

```bash
lp-web-fetch https://example.com
# Should return page content
```

### Test 16: lp-web-search (requires API key)

```bash
# Only if BRAVE_API_KEY is set
[ -n "$BRAVE_API_KEY" ] && lp-web-search "lobster powers" || echo "Skip: no API key"
```

### Test 17: lp-image (requires API key)

```bash
# Only if OPENAI_API_KEY is set
[ -n "$OPENAI_API_KEY" ] && lp-image describe /path/to/image.png || echo "Skip: no API key"
```

### Test 18: lp-browser

```bash
lp-browser screenshot --url https://example.com --output /tmp/screenshot.png
[ -f /tmp/screenshot.png ] && echo "✓ Screenshot created" || echo "✗ Screenshot failed"
rm -f /tmp/screenshot.png
```

---

## Run All Tests

```bash
cd /path/to/lobster-powers
./docs/run-tests.sh
```
