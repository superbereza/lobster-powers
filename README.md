# 🦞 lobster-powers

**Snap snap!** Give your AI agent some serious claws.

> *"Why should OpenClaw have all the fun?"*

Transform any AI agent (Claude Code, Cursor, Copilot, whatever) into a crustacean powerhouse with scheduling, memory, browser automation, and more.

## 🤔 What's the deal?

[OpenClaw](https://openclaw.ai) is an awesome AI assistant with superpowers built-in. But those powers are locked inside the OpenClaw ecosystem.

**lobster-powers** breaks them free! 🦞💥

Same capabilities. Standalone CLI tools. Works everywhere.

## 🔥 The Powers

| Power | CLI | What it does |
|-------|-----|--------------|
| 🕐 **cron** | `lp-cron` | "Remind me to touch grass at 5pm" |
| 🧠 **memory** | `lp-memory` | "What did we decide about auth last month?" |
| 🌐 **browser** | `lp-browser` | "Fill out that form for me" |
| 🗣️ **tts** | `lp-tts` | "Say it out loud" |
| 🔍 **web-search** | `lp-web-search` | "Google this for me" |
| 📄 **web-fetch** | `lp-web-fetch` | "Read that article" |
| 🖼️ **image** | `lp-image` | "What's in this picture?" |
| 🔔 **notify** | `lp-notify` | *ping* |

## 📦 Installation

```bash
# Get everything
pip install lobster-powers[all]

# Or pick your powers
pip install lobster-powers[memory]    # 🧠 Remember stuff
pip install lobster-powers[browser]   # 🌐 Web automation
pip install lobster-powers[tts]       # 🗣️ Talk back
```

## 🚀 Quick Start

```bash
# Set a reminder
lp-cron add "Stand up and stretch!" --at "now + 1 hour"

# Search your notes
lp-memory search "that auth decision"

# Speak!
lp-tts "Hello, I am a lobster with powers"

# Take a screenshot
lp-browser screenshot
```

## 🤖 For AI Agents

Each tool comes with a skill file (`skills/*.md`) that teaches your AI how to use it.

Just ask naturally:
- *"Remind me to deploy at 3pm"*
- *"What did we decide about the database schema?"*
- *"Read that HN article and summarize it"*

## 🏗️ Architecture

```
You ──▶ AI Agent ──▶ lobster-powers CLI ──▶ Magic happens
                         │
                         ├── lp-cron (system at/crontab)
                         ├── lp-memory (OpenAI embeddings + SQLite)
                         ├── lp-browser (Playwright)
                         ├── lp-tts (Edge TTS / OpenAI / ElevenLabs)
                         └── ...
```

No servers. No daemons. Just CLI tools that do their job and get out of the way.

## 🆓 Free Tier Friendly

- **TTS**: Edge TTS is free (300+ Microsoft voices)
- **Memory**: ~$0.01 to index 100 files
- **Search**: Brave API has a free tier

## 📚 Documentation

- [Full Design Doc](docs/DESIGN.md) — All the technical details
- [Skills](skills/) — AI agent instructions

## 🦞 Why "lobster-powers"?

Because:
1. OpenClaw → Claw → Lobster 🦞
2. Lobsters are mass and have superpowers (immortality, basically)
3. The name was available

## 📄 License

MIT — Do whatever you want, just don't blame the lobster.

---

*Made with 🦞 by humans and Claude*
