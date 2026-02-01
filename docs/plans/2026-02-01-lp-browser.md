# lp-browser Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Browser automation via Playwright with daemon architecture.

**Architecture:** Browser runs as background daemon, CLI communicates via Unix socket. Supports accessibility tree snapshots for AI agents.

**Tech Stack:** playwright, asyncio, Unix sockets

---

## Task 1: Create browser daemon with basic lifecycle

**Files:**
- Create: `src/lobster_powers/tools/browser.py`
- Modify: `pyproject.toml`

**Step 1: Write daemon and CLI**

```python
#!/usr/bin/env python3
"""
lp-browser: Browser automation via Playwright.

Examples:
    lp-browser start
    lp-browser open https://example.com
    lp-browser snapshot
    lp-browser click "button[type=submit]"
    lp-browser screenshot
    lp-browser stop
"""

import argparse
import asyncio
import json
import os
import signal
import sys
import tempfile
from pathlib import Path

# State paths
DATA_DIR = Path.home() / ".local" / "share" / "lobster-powers" / "browser"
STATE_FILE = DATA_DIR / "state.json"
SOCKET_PATH = DATA_DIR / "browser.sock"


def load_state() -> dict | None:
    """Load daemon state."""
    if not STATE_FILE.exists():
        return None
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return None


def save_state(state: dict) -> None:
    """Save daemon state."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state))


def clear_state() -> None:
    """Clear daemon state."""
    STATE_FILE.unlink(missing_ok=True)
    SOCKET_PATH.unlink(missing_ok=True)


def is_daemon_running() -> bool:
    """Check if daemon is running."""
    state = load_state()
    if not state:
        return False
    pid = state.get("pid")
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        clear_state()
        return False


async def send_command(command: dict) -> dict:
    """Send command to daemon via socket."""
    reader, writer = await asyncio.open_unix_connection(str(SOCKET_PATH))
    writer.write(json.dumps(command).encode() + b"\n")
    await writer.drain()
    response = await reader.readline()
    writer.close()
    await writer.wait_closed()
    return json.loads(response.decode())


# Daemon implementation

async def run_daemon(headless: bool = False):
    """Run browser daemon."""
    from playwright.async_api import async_playwright

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Start browser
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=headless,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context = await browser.new_context()
    pages = {}  # tab_id -> page
    tab_counter = 0

    # Create initial page
    page = await context.new_page()
    tab_counter += 1
    pages[f"tab_{tab_counter}"] = page
    current_tab = f"tab_{tab_counter}"

    # Save state
    save_state({"pid": os.getpid(), "socket": str(SOCKET_PATH)})

    # Handle commands
    async def handle_client(reader, writer):
        nonlocal current_tab, tab_counter, pages

        try:
            data = await reader.readline()
            if not data:
                return

            cmd = json.loads(data.decode())
            action = cmd.get("action")
            result = {"status": "ok"}

            try:
                page = pages.get(current_tab)

                if action == "status":
                    result["tabs"] = list(pages.keys())
                    result["current"] = current_tab
                    result["url"] = page.url if page else None

                elif action == "open":
                    url = cmd.get("url")
                    if not url.startswith(("http://", "https://")):
                        url = "https://" + url
                    tab_counter += 1
                    new_tab = f"tab_{tab_counter}"
                    new_page = await context.new_page()
                    await new_page.goto(url, wait_until="domcontentloaded")
                    pages[new_tab] = new_page
                    current_tab = new_tab
                    result["tab"] = new_tab
                    result["title"] = await new_page.title()

                elif action == "navigate":
                    url = cmd.get("url")
                    if not url.startswith(("http://", "https://")):
                        url = "https://" + url
                    await page.goto(url, wait_until="domcontentloaded")
                    result["title"] = await page.title()

                elif action == "tabs":
                    result["tabs"] = []
                    for tid, p in pages.items():
                        result["tabs"].append({
                            "id": tid,
                            "url": p.url,
                            "title": await p.title(),
                            "active": tid == current_tab,
                        })

                elif action == "focus":
                    tab_id = cmd.get("tab_id")
                    if tab_id in pages:
                        current_tab = tab_id
                        await pages[tab_id].bring_to_front()
                    else:
                        result = {"status": "error", "error": f"Tab not found: {tab_id}"}

                elif action == "close":
                    tab_id = cmd.get("tab_id") or current_tab
                    if tab_id in pages:
                        await pages[tab_id].close()
                        del pages[tab_id]
                        if tab_id == current_tab and pages:
                            current_tab = list(pages.keys())[0]
                    else:
                        result = {"status": "error", "error": f"Tab not found: {tab_id}"}

                elif action == "snapshot":
                    snapshot = await page.accessibility.snapshot()
                    result["snapshot"] = format_snapshot(snapshot)

                elif action == "screenshot":
                    fd, path = tempfile.mkstemp(suffix=".png")
                    os.close(fd)
                    selector = cmd.get("selector")
                    if selector:
                        element = page.locator(selector)
                        await element.screenshot(path=path)
                    else:
                        await page.screenshot(path=path)
                    result["path"] = path

                elif action == "click":
                    selector = cmd.get("selector")
                    await page.click(selector)

                elif action == "type":
                    selector = cmd.get("selector")
                    text = cmd.get("text")
                    await page.fill(selector, text)

                elif action == "select":
                    selector = cmd.get("selector")
                    value = cmd.get("value")
                    await page.select_option(selector, value)

                elif action == "console":
                    # Return console messages (simplified)
                    result["messages"] = []  # Would need to track these

                elif action == "pdf":
                    fd, path = tempfile.mkstemp(suffix=".pdf")
                    os.close(fd)
                    await page.pdf(path=path)
                    result["path"] = path

                elif action == "stop":
                    result["status"] = "stopping"
                    # Will exit after response

                else:
                    result = {"status": "error", "error": f"Unknown action: {action}"}

            except Exception as e:
                result = {"status": "error", "error": str(e)}

            writer.write(json.dumps(result).encode() + b"\n")
            await writer.drain()

            if action == "stop":
                await browser.close()
                await pw.stop()
                clear_state()
                sys.exit(0)

        finally:
            writer.close()
            await writer.wait_closed()

    # Start server
    SOCKET_PATH.unlink(missing_ok=True)
    server = await asyncio.start_unix_server(handle_client, str(SOCKET_PATH))

    print(f"Browser daemon started (PID: {os.getpid()})")

    # Handle signals
    def signal_handler(sig, frame):
        asyncio.create_task(shutdown())

    async def shutdown():
        await browser.close()
        await pw.stop()
        clear_state()
        server.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    async with server:
        await server.serve_forever()


def format_snapshot(node: dict | None, depth: int = 0) -> str:
    """Format accessibility tree for display."""
    if not node:
        return ""

    lines = []
    indent = "  " * depth
    role = node.get("role", "")
    name = node.get("name", "")

    if role and name:
        lines.append(f"{indent}{role}: {name}")
    elif role:
        lines.append(f"{indent}{role}")

    for child in node.get("children", []):
        lines.append(format_snapshot(child, depth + 1))

    return "\n".join(lines)


# CLI Commands

def cmd_start(args) -> None:
    """Start browser daemon."""
    if is_daemon_running():
        print("Browser daemon already running")
        return

    if args.foreground:
        asyncio.run(run_daemon(headless=args.headless))
    else:
        # Fork to background
        pid = os.fork()
        if pid > 0:
            print(f"Browser daemon started in background (PID: {pid})")
            return
        else:
            # Child process
            os.setsid()
            asyncio.run(run_daemon(headless=args.headless))


def cmd_stop(args) -> None:
    """Stop browser daemon."""
    if not is_daemon_running():
        print("Browser daemon not running")
        return

    result = asyncio.run(send_command({"action": "stop"}))
    print("Browser daemon stopped")


def cmd_status(args) -> None:
    """Show browser status."""
    if not is_daemon_running():
        print("Browser daemon not running")
        return

    result = asyncio.run(send_command({"action": "status"}))
    print(f"Status: running")
    print(f"Current tab: {result.get('current')}")
    print(f"URL: {result.get('url')}")
    print(f"Tabs: {len(result.get('tabs', []))}")


def cmd_open(args) -> None:
    """Open URL in new tab."""
    if not is_daemon_running():
        print("Error: Browser daemon not running. Run: lp-browser start", file=sys.stderr)
        sys.exit(1)

    result = asyncio.run(send_command({"action": "open", "url": args.url}))
    if result.get("status") == "error":
        print(f"Error: {result.get('error')}", file=sys.stderr)
        sys.exit(1)
    print(f"Opened: {result.get('title')}")


def cmd_navigate(args) -> None:
    """Navigate current tab."""
    if not is_daemon_running():
        print("Error: Browser daemon not running", file=sys.stderr)
        sys.exit(1)

    result = asyncio.run(send_command({"action": "navigate", "url": args.url}))
    if result.get("status") == "error":
        print(f"Error: {result.get('error')}", file=sys.stderr)
        sys.exit(1)
    print(f"Navigated to: {result.get('title')}")


def cmd_tabs(args) -> None:
    """List tabs."""
    if not is_daemon_running():
        print("Error: Browser daemon not running", file=sys.stderr)
        sys.exit(1)

    result = asyncio.run(send_command({"action": "tabs"}))
    for tab in result.get("tabs", []):
        active = "*" if tab["active"] else " "
        print(f"{active} {tab['id']}: {tab['title'][:50]} ({tab['url'][:50]})")


def cmd_snapshot(args) -> None:
    """Get accessibility tree."""
    if not is_daemon_running():
        print("Error: Browser daemon not running", file=sys.stderr)
        sys.exit(1)

    result = asyncio.run(send_command({"action": "snapshot"}))
    if result.get("status") == "error":
        print(f"Error: {result.get('error')}", file=sys.stderr)
        sys.exit(1)
    print(result.get("snapshot", ""))


def cmd_screenshot(args) -> None:
    """Take screenshot."""
    if not is_daemon_running():
        print("Error: Browser daemon not running", file=sys.stderr)
        sys.exit(1)

    cmd = {"action": "screenshot"}
    if args.selector:
        cmd["selector"] = args.selector

    result = asyncio.run(send_command(cmd))
    if result.get("status") == "error":
        print(f"Error: {result.get('error')}", file=sys.stderr)
        sys.exit(1)
    print(f"Screenshot saved: {result.get('path')}")


def cmd_click(args) -> None:
    """Click element."""
    if not is_daemon_running():
        print("Error: Browser daemon not running", file=sys.stderr)
        sys.exit(1)

    result = asyncio.run(send_command({"action": "click", "selector": args.selector}))
    if result.get("status") == "error":
        print(f"Error: {result.get('error')}", file=sys.stderr)
        sys.exit(1)
    print("Clicked")


def cmd_type(args) -> None:
    """Type into element."""
    if not is_daemon_running():
        print("Error: Browser daemon not running", file=sys.stderr)
        sys.exit(1)

    result = asyncio.run(send_command({
        "action": "type",
        "selector": args.selector,
        "text": args.text
    }))
    if result.get("status") == "error":
        print(f"Error: {result.get('error')}", file=sys.stderr)
        sys.exit(1)
    print("Typed")


def cmd_pdf(args) -> None:
    """Save page as PDF."""
    if not is_daemon_running():
        print("Error: Browser daemon not running", file=sys.stderr)
        sys.exit(1)

    result = asyncio.run(send_command({"action": "pdf"}))
    if result.get("status") == "error":
        print(f"Error: {result.get('error')}", file=sys.stderr)
        sys.exit(1)
    print(f"PDF saved: {result.get('path')}")


def main():
    parser = argparse.ArgumentParser(
        description="Browser automation via Playwright",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # start
    start_p = subparsers.add_parser("start", help="Start browser daemon")
    start_p.add_argument("--headless", action="store_true", help="Run headless")
    start_p.add_argument("--foreground", "-f", action="store_true", help="Run in foreground")
    start_p.set_defaults(func=cmd_start)

    # stop
    stop_p = subparsers.add_parser("stop", help="Stop browser daemon")
    stop_p.set_defaults(func=cmd_stop)

    # status
    status_p = subparsers.add_parser("status", help="Show status")
    status_p.set_defaults(func=cmd_status)

    # open
    open_p = subparsers.add_parser("open", help="Open URL in new tab")
    open_p.add_argument("url", help="URL to open")
    open_p.set_defaults(func=cmd_open)

    # navigate
    nav_p = subparsers.add_parser("navigate", help="Navigate current tab")
    nav_p.add_argument("url", help="URL to navigate to")
    nav_p.set_defaults(func=cmd_navigate)

    # tabs
    tabs_p = subparsers.add_parser("tabs", help="List tabs")
    tabs_p.set_defaults(func=cmd_tabs)

    # snapshot
    snap_p = subparsers.add_parser("snapshot", help="Get accessibility tree")
    snap_p.set_defaults(func=cmd_snapshot)

    # screenshot
    ss_p = subparsers.add_parser("screenshot", help="Take screenshot")
    ss_p.add_argument("--selector", "-s", help="Element selector")
    ss_p.set_defaults(func=cmd_screenshot)

    # click
    click_p = subparsers.add_parser("click", help="Click element")
    click_p.add_argument("selector", help="CSS selector")
    click_p.set_defaults(func=cmd_click)

    # type
    type_p = subparsers.add_parser("type", help="Type into element")
    type_p.add_argument("selector", help="CSS selector")
    type_p.add_argument("text", help="Text to type")
    type_p.set_defaults(func=cmd_type)

    # pdf
    pdf_p = subparsers.add_parser("pdf", help="Save as PDF")
    pdf_p.set_defaults(func=cmd_pdf)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

**Step 2: Update pyproject.toml**

Add to `[project.scripts]`:
```toml
lp-browser = "lobster_powers.tools.browser:main"
```

Add to `[project.optional-dependencies]`:
```toml
browser = ["playwright"]
```

**Step 3: Install and test**

```bash
pip install -e ".[browser]"
playwright install chromium

# Start daemon
lp-browser start

# Test commands
lp-browser open https://example.com
lp-browser snapshot
lp-browser screenshot
lp-browser tabs

# Stop
lp-browser stop
```

**Step 4: Commit**

```bash
git add src/lobster_powers/tools/browser.py pyproject.toml
git commit -m "feat(browser): add lp-browser with Playwright daemon"
```

---

## Task 2: Create skill file

**Files:**
- Create: `skills/browser.md`

**Step 1: Write skill file**

```markdown
---
name: browser
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
```

**Step 2: Commit**

```bash
git add skills/browser.md
git commit -m "docs(browser): add skill file"
```

---

## Summary

Total: 2 tasks, ~450 lines of code.

Estimated time: 45-60 minutes.

---

## Future Tasks (Phase 2-4)

These are documented in DESIGN.md but not implemented in this plan:

- **Phase 2: Docker Sandbox** - Isolated browser in container
- **Phase 3: Chrome Extension Relay** - Connect to existing Chrome
- **Phase 4: Node Proxy** - Remote browser on different machine
