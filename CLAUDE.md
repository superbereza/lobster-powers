# lobster-powers - Claude Runtime Context

Python port of OpenClaw native tools as standalone CLIs.

## Quick Reference

| Tool | CLI | Status | OpenClaw Source |
|------|-----|--------|-----------------|
| Cron | `lp-cron` | Done | cron-tool.ts |
| Memory | `lp-memory` | TODO | memory-tool.ts |
| TTS | `lp-tts` | TODO | tts.ts |
| Image | `lp-image` | TODO | image-tool.ts |
| Web Fetch | `lp-web-fetch` | TODO | web-fetch.ts |
| Web Search | `lp-web-search` | TODO | web-search.ts |
| Browser | `lp-browser` | TODO | browser-tool.ts |
| Notify | `lp-notify` | TODO | (system) |

## Architecture

```
~/.config/lobster-powers/
└── config.json              # API keys, preferences

~/.local/share/lobster-powers/
├── cron-jobs.json           # Scheduled jobs
├── memory/
│   └── index.db             # SQLite with embeddings
└── browser/
    └── profiles/            # Browser profiles
```

## Development

```bash
# Install in dev mode
cd /home/superbereza/dev/lobster-powers
pip install -e ".[all]"

# Test CLI
lp-cron list
lp-memory search "test"
```

## Implementation Pattern

Each tool follows the same structure:

```python
# src/lobster_powers/tools/example.py
import argparse
import json
from pathlib import Path

DATA_DIR = Path.home() / ".local" / "share" / "lobster-powers"

def cmd_action(args):
    """Subcommand handler."""
    pass

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    action_parser = subparsers.add_parser("action")
    action_parser.add_argument("arg")
    action_parser.set_defaults(func=cmd_action)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
```

## Provider Priority

For tools with multiple providers:

1. Check config file preference
2. Check available API keys
3. Fall back to free option (Edge TTS, etc.)

## Key Files

```
src/lobster_powers/
├── __init__.py
├── config.py                # Config management
└── tools/
    ├── cron.py              # lp-cron (DONE)
    ├── memory.py            # lp-memory (TODO: rewrite)
    ├── tts.py               # lp-tts
    ├── image.py             # lp-image
    ├── web_fetch.py         # lp-web-fetch
    ├── web_search.py        # lp-web-search
    ├── browser.py           # lp-browser
    └── notify.py            # lp-notify

skills/                      # Skill files for AI agents
├── cron.md
├── memory.md
└── ...
```

## See Also

- `docs/DESIGN.md` - Full implementation design (1000+ lines)
- OpenClaw source: `/home/superbereza/dev/openclaw/src/agents/tools/`
