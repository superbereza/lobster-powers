# openclaw-tools-mcp

OpenClaw tools as MCP server for Claude Code.

Use powerful OpenClaw tools (cron, browser, memory) directly in Claude Code via MCP protocol.

## Features

- **Cron** — Schedule tasks and reminders
- **Memory** — Semantic search across your notes
- **Browser** — Web automation with Playwright (coming soon)

## Installation

```bash
# Install as Claude Code plugin
claude plugin install openclaw-tools-mcp

# Or manually
pip install openclaw-tools-mcp
```

## Usage

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "openclaw": {
      "command": "python",
      "args": ["-m", "openclaw_tools_mcp"]
    }
  }
}
```

## Requirements

- Python 3.11+
- OpenClaw Gateway running (for tool execution)

## How it works

```
Claude Code
    │
    │ MCP protocol
    ▼
openclaw-tools-mcp (this package)
    │
    │ HTTP/WebSocket
    ▼
OpenClaw Gateway (executes tools)
```

## License

MIT
