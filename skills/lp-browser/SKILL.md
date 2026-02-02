---
name: lp-browser
description: Browser automation using lp-browser CLI with Playwright
---

# Browser - Web Automation

Use `lp-browser` to automate web interactions.

## Quick Start

```bash
# Start browser (required first)
lp-browser start

# Open a page
lp-browser open https://example.com

# Get accessibility tree (for understanding page structure)
lp-browser snapshot

# Interact
lp-browser click "button[type=submit]"
lp-browser type "#email" "user@example.com"

# Capture
lp-browser screenshot
lp-browser pdf

# Stop when done
lp-browser stop
```

## Commands

| Command | Description |
|---------|-------------|
| `lp-browser start` | Start browser daemon |
| `lp-browser stop` | Stop browser daemon |
| `lp-browser status` | Show current status |
| `lp-browser open <url>` | Open URL in new tab |
| `lp-browser navigate <url>` | Navigate current tab |
| `lp-browser tabs` | List all tabs |
| `lp-browser snapshot` | Get accessibility tree |
| `lp-browser screenshot` | Take screenshot |
| `lp-browser click <selector>` | Click element |
| `lp-browser type <selector> <text>` | Type into element |
| `lp-browser pdf` | Save page as PDF |

## Workflow

1. **Start**: `lp-browser start`
2. **Navigate**: `lp-browser open https://...`
3. **Inspect**: `lp-browser snapshot` to understand page
4. **Interact**: click, type, select
5. **Capture**: screenshot or pdf
6. **Stop**: `lp-browser stop`

## Tips

- Always start with `snapshot` to understand page structure
- Use CSS selectors for elements: `#id`, `.class`, `button[type=submit]`
- The daemon persists between commands - no need to restart
- Use `--headless` for server environments
