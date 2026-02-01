# lobster-powers 🦞💪

OpenClaw superpowers for any AI agent.

Turn Claude Code, Cursor, or any LLM into a full-featured personal assistant with cron jobs, memory search, browser automation, and more.

## What is this?

OpenClaw is a powerful personal AI assistant with native tools like scheduling, memory, and browser control. But those tools only work inside OpenClaw.

**lobster-powers** extracts these capabilities as standalone CLI tools + skills that work with any AI agent.

## Available Powers

| Power | CLI | What it does |
|-------|-----|--------------|
| **cron** | `lp-cron` | Schedule reminders and recurring tasks |
| **memory** | `lp-memory` | Semantic search over your notes and files |
| **browser** | `lp-browser` | Automate web interactions |
| **tts** | `lp-speak` | Text-to-speech |
| **notify** | `lp-notify` | System notifications |

## Installation

```bash
pip install lobster-powers
```

Or install specific tools:
```bash
pip install lobster-powers[cron]
pip install lobster-powers[memory]
pip install lobster-powers[browser]
```

## Usage with Claude Code

Skills are automatically available. Just ask Claude to:
- "Remind me to check PRs tomorrow at 9am"
- "Search my notes for that decision about authentication"
- "Take a screenshot of the current page"

## License

MIT
