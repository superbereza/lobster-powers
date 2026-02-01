# lobster-powers Design Document

**Version:** 1.0
**Date:** 2026-02-01

Python port of OpenClaw native tools as standalone CLIs.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [lp-cron](#lp-cron)
4. [lp-memory](#lp-memory)
5. [lp-tts](#lp-tts)
6. [lp-image](#lp-image)
7. [lp-web-fetch](#lp-web-fetch)
8. [lp-web-search](#lp-web-search)
9. [lp-browser](#lp-browser)
10. [lp-notify](#lp-notify)
11. [Configuration](#configuration)
12. [Installation](#installation)

---

## Overview

**lobster-powers** brings OpenClaw superpowers to any AI agent without requiring the OpenClaw Gateway.

Each tool is:
- **Standalone CLI** (`lp-*`) — works from any terminal
- **Skill file** (`skills/*.md`) — instructions for AI agents

### Design Principles

1. **Same interface as OpenClaw** — agents trained on OpenClaw skills work unchanged
2. **No Gateway dependency** — uses system tools and APIs directly
3. **Graceful degradation** — free fallbacks when API keys unavailable
4. **Single config file** — `~/.config/lobster-powers/config.json`

---

## Architecture

```
~/.config/lobster-powers/
├── config.json              # API keys, preferences
└── settings/
    └── tts.json             # TTS user preferences

~/.local/share/lobster-powers/
├── cron-jobs.json           # Scheduled jobs
├── memory/
│   ├── index.db             # SQLite with embeddings
│   └── cache/               # Embedding cache
└── browser/
    └── profiles/            # Browser profiles
```

### Dependencies

```toml
[project.optional-dependencies]
core = []  # No deps for cron, notify
memory = ["openai", "numpy"]
tts = ["openai", "httpx", "edge-tts"]
image = ["openai", "httpx", "pillow"]
web = ["httpx", "readability-lxml", "lxml"]
browser = ["playwright"]
all = ["lobster-powers[memory,tts,image,web,browser]"]
```

---

## lp-cron

**Source:** OpenClaw `cron-tool.ts` (~315 lines)

Schedule reminders and recurring tasks using system `at` and `crontab`.

### CLI

```bash
lp-cron status                           # Check scheduler status
lp-cron list [--all]                     # List jobs (--all includes disabled)
lp-cron add "text" --at "9am tomorrow"   # One-time reminder
lp-cron add "text" --cron "0 9 * * *"    # Recurring job
lp-cron add "text" --every 30m           # Every 30 minutes
lp-cron update <id> --text "new text"    # Update job
lp-cron remove <id>                      # Delete job
lp-cron run <id>                         # Trigger immediately
lp-cron runs <id>                        # Show run history
```

### Schedule Types

| Type | OpenClaw | lobster-powers |
|------|----------|----------------|
| One-shot | `schedule.kind: "at"` | `at` command |
| Recurring | `schedule.kind: "cron"` | `crontab` |
| Interval | `schedule.kind: "every"` | `crontab` (converted) |

### Payload Types

OpenClaw has `systemEvent` (inject text) and `agentTurn` (run agent). Without Gateway, we simplify:

| OpenClaw | lobster-powers |
|----------|----------------|
| `systemEvent` | `notify-send` notification |
| `agentTurn` | Run shell command (optional `--exec`) |

### Storage

```json
{
  "jobs": [
    {
      "id": "job_abc123",
      "text": "Check PRs",
      "type": "at",
      "schedule": "9:00 tomorrow",
      "at_job_id": "42",
      "created": "2026-01-15T10:30:00Z",
      "enabled": true,
      "runs": [
        {"timestamp": "2026-01-16T09:00:00Z", "status": "success"}
      ]
    }
  ],
  "next_id": 2
}
```

### Algorithm: add

```python
def cmd_add(text, at=None, cron=None, every=None, exec_cmd=None):
    job = create_job(text)

    if at:
        # Use system `at` command
        notify_cmd = f'notify-send "🦞 Reminder" "{text}"'
        if exec_cmd:
            notify_cmd += f' && {exec_cmd}'
        result = subprocess.run(["at", at], input=notify_cmd, text=True, capture_output=True)
        job["at_job_id"] = parse_at_job_id(result.stderr)

    elif cron:
        # Add to crontab with marker
        cron_line = f'{cron} notify-send "🦞 Reminder" "{text}" # lp-cron-{job["id"]}'
        add_to_crontab(cron_line)

    elif every:
        # Convert interval to cron (e.g., "30m" -> "*/30 * * * *")
        cron_expr = interval_to_cron(every)
        # ... same as cron

    save_job(job)
```

### Error Handling

- `at` not installed → `sudo apt install at`
- crontab empty → create new
- Invalid schedule → clear error message with examples

---

## lp-memory

**Source:** OpenClaw `memory-tool.ts` + `sync-memory-files.ts` (~600 lines)

Semantic search over notes using OpenAI embeddings + SQLite.

### CLI

```bash
lp-memory index <path>                    # Index file or directory
lp-memory search "query" [--top 5]        # Semantic search
lp-memory read <file> --from 42 --lines 20 # Read specific lines
lp-memory status                          # Index statistics
lp-memory forget <path>                   # Remove from index
lp-memory reindex                         # Force full reindex
```

### Index Flow

```
1. Scan MEMORY.md + memory/*.md + extraPaths
2. For each file:
   a. Compute SHA256 hash
   b. Skip if hash unchanged
   c. Split into chunks (~500 chars, paragraph-aware)
   d. Batch API call: POST /v1/embeddings
   e. Store chunks + embeddings in SQLite
```

### SQLite Schema

```sql
-- Files metadata
CREATE TABLE files (
    path TEXT PRIMARY KEY,
    hash TEXT NOT NULL,
    mtime INTEGER NOT NULL,
    source TEXT DEFAULT 'memory'  -- 'memory' | 'extra'
);

-- Text chunks with embeddings
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding BLOB NOT NULL,  -- float32 array, 1536 dims
    FOREIGN KEY (path) REFERENCES files(path) ON DELETE CASCADE
);

CREATE INDEX idx_chunks_path ON chunks(path);

-- FTS5 virtual table for text search
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    content,
    content='chunks',
    content_rowid='id'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, content) VALUES (new.id, new.content);
END;
CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES('delete', old.id, old.content);
END;
CREATE TRIGGER chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES('delete', old.id, old.content);
    INSERT INTO chunks_fts(rowid, content) VALUES (new.id, new.content);
END;
```

### Hybrid Search (Vector + FTS)

OpenClaw uses hybrid search combining semantic (vector) and keyword (FTS) matching.

```python
def hybrid_search(
    query: str,
    top_k: int = 5,
    vector_weight: float = 0.7,  # 70% vector, 30% text
    text_weight: float = 0.3
) -> list[SearchResult]:
    """
    Hybrid search combining vector similarity and FTS ranking.

    This matches OpenClaw's approach for better recall on exact terms
    while maintaining semantic understanding.
    """
    # 1. Vector search
    query_embedding = get_embedding(query)
    vector_results = vector_search(query_embedding, top_k=top_k * 2)

    # 2. FTS search
    fts_results = db.execute("""
        SELECT c.*, bm25(chunks_fts) as fts_score
        FROM chunks_fts
        JOIN chunks c ON chunks_fts.rowid = c.id
        WHERE chunks_fts MATCH ?
        ORDER BY bm25(chunks_fts)
        LIMIT ?
    """, (fts_escape(query), top_k * 2)).fetchall()

    # 3. Normalize scores to [0, 1]
    vector_scores = normalize_scores({r.id: r.score for r in vector_results})
    fts_scores = normalize_scores({r.id: -r.fts_score for r in fts_results})  # BM25 is negative

    # 4. Combine with weights
    all_ids = set(vector_scores.keys()) | set(fts_scores.keys())
    combined = {}
    for chunk_id in all_ids:
        v_score = vector_scores.get(chunk_id, 0)
        t_score = fts_scores.get(chunk_id, 0)
        combined[chunk_id] = (v_score * vector_weight) + (t_score * text_weight)

    # 5. Return top-k by combined score
    sorted_ids = sorted(combined.keys(), key=lambda x: combined[x], reverse=True)
    return [get_chunk(id) for id in sorted_ids[:top_k]]


def fts_escape(query: str) -> str:
    """Escape special FTS5 characters."""
    # Convert natural language to FTS query
    # "what auth method" -> "what OR auth OR method"
    words = query.split()
    return " OR ".join(f'"{w}"' for w in words if len(w) > 2)


def normalize_scores(scores: dict[int, float]) -> dict[int, float]:
    """Normalize scores to [0, 1] range."""
    if not scores:
        return {}
    min_s = min(scores.values())
    max_s = max(scores.values())
    if max_s == min_s:
        return {k: 1.0 for k in scores}
    return {k: (v - min_s) / (max_s - min_s) for k, v in scores.items()}
```

### Search CLI Options

```bash
lp-memory search "query"                  # Hybrid search (default)
lp-memory search "query" --vector-only    # Only vector similarity
lp-memory search "query" --fts-only       # Only keyword matching
lp-memory search "query" --vector-weight 0.5  # Custom weights
```

### Output Format

```
Found 3 matches:

[0.89] notes/2024-01-15.md:42-48
  We decided to use JWT for authentication because...

[0.76] MEMORY.md:12-15
  Auth: JWT tokens, 24h expiry, refresh via cookie
```

### Cost Estimate

- Model: `text-embedding-3-small` ($0.02 / 1M tokens)
- Index 100 files (~50KB each): ~$0.01
- 1000 searches/month: ~$0.10

---

## lp-tts

**Source:** OpenClaw `tts.ts` (~1600 lines)

Text-to-speech with multiple providers.

### CLI

```bash
lp-tts "Hello world"                      # Speak text (default provider)
lp-tts "Hello" --provider openai          # Use OpenAI
lp-tts "Hello" --provider elevenlabs      # Use ElevenLabs
lp-tts "Hello" --provider edge            # Use Edge TTS (free)
lp-tts "Hello" --voice alloy              # Specify voice
lp-tts "Hello" --output voice.mp3         # Save to file
lp-tts status                             # Show current settings
lp-tts set provider edge                  # Change default provider
lp-tts set max-length 1500                # Set max text length
lp-tts voices                             # List available voices
```

### Providers

| Provider | API Key | Cost | Voices |
|----------|---------|------|--------|
| **edge** (default) | None | Free | 300+ (Microsoft) |
| openai | `OPENAI_API_KEY` | $15/1M chars | alloy, ash, coral, echo, fable, onyx, nova, sage, shimmer |
| elevenlabs | `ELEVENLABS_API_KEY` | $0.30/1K chars | Custom clones |

### Provider Selection

```python
def get_provider():
    # 1. Check user preference
    prefs = load_prefs()
    if prefs.get("provider"):
        return prefs["provider"]

    # 2. Check available API keys
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("ELEVENLABS_API_KEY"):
        return "elevenlabs"

    # 3. Fall back to free Edge TTS
    return "edge"
```

### Edge TTS (Free)

Uses `edge-tts` Python package (Microsoft Edge voices, no API key).

```python
import edge_tts

async def edge_tts_speak(text: str, voice: str = "en-US-MichelleNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("output.mp3")
```

### OpenAI TTS

```python
from openai import OpenAI

def openai_tts(text: str, voice: str = "alloy", model: str = "gpt-4o-mini-tts"):
    client = OpenAI()
    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        response_format="mp3"
    )
    response.stream_to_file("output.mp3")
```

### ElevenLabs TTS

```python
import httpx

def elevenlabs_tts(text: str, voice_id: str, api_key: str):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    response = httpx.post(url,
        headers={"xi-api-key": api_key},
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
    )
    with open("output.mp3", "wb") as f:
        f.write(response.content)
```

### Auto-summarization

When text exceeds `max-length` (default 1500 chars):

```python
def maybe_summarize(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text

    # Use LLM to summarize
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Summarize to ~{max_length} chars:\n\n{text}"
        }],
        max_tokens=max_length // 2
    )
    return response.choices[0].message.content
```

### TTS Directives (как в OpenClaw)

Агент может встраивать директивы в текст для контроля TTS:

```
[[tts:provider=openai voice=alloy]]
Hello, this will be spoken with OpenAI alloy voice.

[[tts:text]]This is the actual text to speak[[/tts:text]]
But this text will be shown to the user, not spoken.
```

#### Supported Directives

| Directive | Description | Example |
|-----------|-------------|---------|
| `provider` | TTS provider | `provider=openai` |
| `voice` | OpenAI voice | `voice=alloy` |
| `voiceId` | ElevenLabs voice ID | `voiceId=pMsXgVXv3BLzUgSXRplE` |
| `model` | Model ID | `model=eleven_multilingual_v2` |
| `stability` | ElevenLabs stability (0-1) | `stability=0.5` |
| `similarity` | ElevenLabs similarity boost (0-1) | `similarity=0.75` |
| `style` | ElevenLabs style (0-1) | `style=0.3` |
| `speed` | ElevenLabs speed (0.5-2) | `speed=1.2` |
| `seed` | ElevenLabs seed for reproducibility | `seed=42` |

#### Parsing Implementation

```python
import re
from dataclasses import dataclass

@dataclass
class TtsDirectives:
    provider: str | None = None
    voice: str | None = None
    voice_id: str | None = None
    model: str | None = None
    stability: float | None = None
    similarity: float | None = None
    style: float | None = None
    speed: float | None = None
    seed: int | None = None
    tts_text: str | None = None  # Explicit text to speak


def parse_tts_directives(text: str) -> tuple[str, TtsDirectives]:
    """
    Parse TTS directives from text.

    Returns (cleaned_text, directives).
    """
    directives = TtsDirectives()
    cleaned = text

    # Extract [[tts:text]]...[[/tts:text]] block
    text_match = re.search(
        r'\[\[tts:text\]\](.*?)\[\[/tts:text\]\]',
        cleaned,
        re.DOTALL
    )
    if text_match:
        directives.tts_text = text_match.group(1).strip()
        cleaned = cleaned[:text_match.start()] + cleaned[text_match.end():]

    # Extract [[tts:key=value ...]] directives
    directive_pattern = r'\[\[tts:([^\]]+)\]\]'
    for match in re.finditer(directive_pattern, cleaned):
        body = match.group(1)
        for token in body.split():
            if '=' not in token:
                continue
            key, value = token.split('=', 1)
            key = key.lower().strip()
            value = value.strip()

            if key == 'provider':
                directives.provider = value
            elif key == 'voice':
                directives.voice = value
            elif key in ('voiceid', 'voice_id'):
                directives.voice_id = value
            elif key == 'model':
                directives.model = value
            elif key == 'stability':
                directives.stability = float(value)
            elif key in ('similarity', 'similarityboost'):
                directives.similarity = float(value)
            elif key == 'style':
                directives.style = float(value)
            elif key == 'speed':
                directives.speed = float(value)
            elif key == 'seed':
                directives.seed = int(value)

    # Remove all directive tags from cleaned text
    cleaned = re.sub(directive_pattern, '', cleaned).strip()

    return cleaned, directives


def apply_directives(base_config: TtsConfig, directives: TtsDirectives) -> TtsConfig:
    """Merge directives into base config."""
    config = base_config.copy()

    if directives.provider:
        config.provider = directives.provider
    if directives.voice:
        config.openai_voice = directives.voice
    if directives.voice_id:
        config.elevenlabs_voice_id = directives.voice_id
    # ... etc

    return config
```

#### Auto Modes

| Mode | Behavior |
|------|----------|
| `off` | TTS disabled |
| `always` | Always generate audio |
| `inbound` | Only when user sent audio |
| `tagged` | Only when `[[tts:...]]` present |

```bash
lp-tts set auto-mode tagged              # Only speak when tagged
lp-tts set auto-mode always              # Always speak
```

---

## lp-image

**Source:** OpenClaw `image-tool.ts` (~450 lines)

Analyze images using vision models.

### CLI

```bash
lp-image analyze photo.jpg                # Describe image
lp-image analyze photo.jpg "What color?"  # Ask specific question
lp-image analyze https://... "prompt"     # From URL
lp-image --model openai photo.jpg         # Use specific provider
```

### Providers

| Provider | Model | Cost |
|----------|-------|------|
| openai (default) | gpt-4o-mini | $0.075/image |
| anthropic | claude-opus-4-5 | $0.08/image |

### Implementation

```python
import base64
from openai import OpenAI

def analyze_image(image_path: str, prompt: str = "Describe the image."):
    client = OpenAI()

    # Load image
    if image_path.startswith("http"):
        image_data = {"type": "image_url", "image_url": {"url": image_path}}
    else:
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode()
        image_data = {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
        }

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                image_data
            ]
        }],
        max_tokens=512
    )
    return response.choices[0].message.content
```

---

## lp-web-fetch

**Source:** OpenClaw `web-fetch.ts` (~655 lines)

Fetch and extract readable content from URLs.

### CLI

```bash
lp-web-fetch https://example.com          # Fetch as markdown
lp-web-fetch https://... --text           # Fetch as plain text
lp-web-fetch https://... --max-chars 5000 # Limit output
```

### Implementation

```python
import httpx
from readability import Document

def web_fetch(url: str, extract_mode: str = "markdown", max_chars: int = 50000):
    # Fetch with timeout and redirects
    response = httpx.get(url, follow_redirects=True, timeout=30)

    content_type = response.headers.get("content-type", "")

    if "text/html" in content_type:
        # Extract readable content
        doc = Document(response.text)
        title = doc.title()
        content = doc.summary()

        if extract_mode == "text":
            # Strip HTML
            from bs4 import BeautifulSoup
            content = BeautifulSoup(content, "html.parser").get_text()
        else:
            # Convert to markdown
            import html2text
            h = html2text.HTML2Text()
            content = h.handle(content)

    elif "application/json" in content_type:
        import json
        content = json.dumps(response.json(), indent=2)

    else:
        content = response.text

    # Truncate if needed
    if len(content) > max_chars:
        content = content[:max_chars] + "\n\n[truncated]"

    return {"title": title, "content": content, "url": str(response.url)}
```

### Firecrawl Fallback

When Readability fails (JavaScript-heavy pages):

```python
def firecrawl_fetch(url: str, api_key: str):
    response = httpx.post(
        "https://api.firecrawl.dev/v2/scrape",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"url": url, "formats": ["markdown"]}
    )
    return response.json()["data"]["markdown"]
```

---

## lp-web-search

**Source:** OpenClaw `web-search.ts` (~540 lines)

Web search with multiple providers.

### CLI

```bash
lp-web-search "python async tutorial"     # Search (default provider)
lp-web-search "query" --provider brave    # Use Brave
lp-web-search "query" --provider perplexity  # Use Perplexity
lp-web-search "query" --count 10          # More results
lp-web-search "query" --freshness pw      # Past week (Brave)
```

### Providers

| Provider | API Key | Features |
|----------|---------|----------|
| brave | `BRAVE_API_KEY` | Fast, freshness filter |
| perplexity | `PERPLEXITY_API_KEY` | AI-synthesized answers |

### Brave Search

```python
def brave_search(query: str, api_key: str, count: int = 5):
    response = httpx.get(
        "https://api.search.brave.com/res/v1/web/search",
        params={"q": query, "count": count},
        headers={"X-Subscription-Token": api_key}
    )
    data = response.json()
    return [
        {
            "title": r["title"],
            "url": r["url"],
            "description": r["description"]
        }
        for r in data["web"]["results"]
    ]
```

### Perplexity Search

```python
def perplexity_search(query: str, api_key: str):
    response = httpx.post(
        "https://api.perplexity.ai/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "sonar-pro",
            "messages": [{"role": "user", "content": query}]
        }
    )
    data = response.json()
    return {
        "content": data["choices"][0]["message"]["content"],
        "citations": data.get("citations", [])
    }
```

---

## lp-browser

**Source:** OpenClaw `browser-tool.ts` + `pw-tools-core.ts` (~1400 lines)

Browser automation via Playwright.

### CLI

```bash
# Lifecycle
lp-browser start                          # Start browser
lp-browser stop                           # Stop browser
lp-browser status                         # Show status

# Navigation
lp-browser open https://example.com       # Open URL
lp-browser navigate https://...           # Navigate current tab
lp-browser tabs                           # List tabs
lp-browser focus <tab-id>                 # Switch tab
lp-browser close [tab-id]                 # Close tab

# Inspection
lp-browser snapshot                       # Get accessibility tree
lp-browser screenshot [--element "sel"]   # Take screenshot
lp-browser console                        # Get console logs
lp-browser pdf                            # Save as PDF

# Interaction
lp-browser click "button[type=submit]"    # Click element
lp-browser type "#input" "text"           # Type into element
lp-browser select "#dropdown" "value"     # Select option
lp-browser upload "#file" /path/to/file   # Upload file
lp-browser dialog accept                  # Handle dialog
```

### Architecture

```
┌─────────────────┐      ┌─────────────────┐
│   lp-browser    │──────│   Playwright    │
│   (Python CLI)  │      │   (Browser)     │
└─────────────────┘      └─────────────────┘
         │
         │  Unix socket / HTTP
         ▼
┌─────────────────┐
│  Browser State  │
│  (~/.local/     │
│  share/lp/      │
│  browser/)      │
└─────────────────┘
```

### State Management

Browser runs as background process, CLI communicates via socket:

```python
# Start browser daemon
async def start_browser():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,  # or True for server
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = await browser.new_context()

    # Save state
    state = {"pid": os.getpid(), "socket": "/tmp/lp-browser.sock"}
    save_state(state)

    # Start socket server
    await start_socket_server(context)
```

### Snapshot (Accessibility Tree)

```python
async def get_snapshot(page):
    """Get accessibility tree for AI agents."""
    snapshot = await page.accessibility.snapshot()

    def format_node(node, depth=0):
        indent = "  " * depth
        role = node.get("role", "")
        name = node.get("name", "")
        ref = f"[{node.get('ref', '')}]" if "ref" in node else ""

        line = f"{indent}{role}: {name} {ref}"

        children = node.get("children", [])
        child_lines = [format_node(c, depth + 1) for c in children]

        return "\n".join([line] + child_lines)

    return format_node(snapshot)
```

### Phases

| Phase | Feature | Description |
|-------|---------|-------------|
| 1 | Basic CLI | Playwright daemon + socket |
| 2 | Sandbox | Docker isolation |
| 3 | Extension Relay | Connect to existing Chrome |
| 4 | Node Proxy | Remote browser on different machine |

---

#### Phase 2: Docker Sandbox

Изолированный браузер в Docker контейнере для безопасности.

```bash
lp-browser start --sandbox              # Start in Docker
lp-browser start --target host          # Direct on host (default)
```

**Архитектура:**

```
┌─────────────────┐     ┌──────────────────────────────┐
│   lp-browser    │────▶│  Docker Container            │
│   (CLI)         │     │  ┌────────────────────────┐  │
└─────────────────┘     │  │  Playwright + Chromium │  │
        ▲               │  └────────────────────────┘  │
        │ WebSocket     │  Port 9222 (CDP)             │
        └───────────────┴──────────────────────────────┘
```

**Dockerfile:**

```dockerfile
FROM mcr.microsoft.com/playwright:v1.40.0-jammy

WORKDIR /app
COPY browser_server.py .

# Expose CDP port
EXPOSE 9222

CMD ["python", "browser_server.py", "--port", "9222"]
```

**Преимущества:**
- Изоляция от хостовой системы
- Нет доступа к файлам пользователя
- Можно ограничить сеть
- Легко пересоздать чистое окружение

---

#### Phase 3: Chrome Extension Relay

Подключение к существующему Chrome с расширением. Позволяет использовать авторизованные сессии пользователя.

```bash
lp-browser start --relay                # Connect to existing Chrome
lp-browser relay status                 # Check extension connection
```

**Компоненты:**

```
┌─────────────────┐     ┌─────────────────────────────────┐
│   lp-browser    │     │  User's Chrome                  │
│   (CLI)         │     │  ┌───────────────────────────┐  │
└────────┬────────┘     │  │  Lobster Extension        │  │
         │              │  │  - Native messaging       │  │
         │ WebSocket    │  │  - Tab control            │  │
         └─────────────▶│  │  - Cookie access          │  │
                        │  └───────────────────────────┘  │
                        └─────────────────────────────────┘
```

**Chrome Extension (manifest.json):**

```json
{
  "manifest_version": 3,
  "name": "Lobster Powers Relay",
  "version": "1.0",
  "permissions": [
    "tabs",
    "activeTab",
    "scripting",
    "nativeMessaging"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "externally_connectable": {
    "ids": ["*"],
    "matches": ["*://localhost/*"]
  }
}
```

**Native Messaging Host:**

```python
# ~/.config/lobster-powers/browser/native_host.py
import json
import struct
import sys

def read_message():
    raw_length = sys.stdin.buffer.read(4)
    length = struct.unpack('I', raw_length)[0]
    message = sys.stdin.buffer.read(length).decode('utf-8')
    return json.loads(message)

def send_message(message):
    encoded = json.dumps(message).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('I', len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()
```

**Use Cases:**
- Автоматизация на залогиненных сайтах
- Использование cookies/sessions пользователя
- Работа с сайтами, блокирующими Playwright

---

#### Phase 4: Node Proxy

Удалённый браузер на другой машине. Полезно для:
- Другой IP (обход гео-блокировок)
- Больше ресурсов (GPU для рендеринга)
- Headless сервер

```bash
# На сервере
lp-browser serve --host 0.0.0.0 --port 9222 --token SECRET

# На клиенте
lp-browser start --proxy ws://server:9222 --token SECRET
```

**Архитектура:**

```
┌─────────────────┐              ┌─────────────────────────┐
│  Local Machine  │              │  Remote Server          │
│  ┌───────────┐  │   WebSocket  │  ┌───────────────────┐  │
│  │ lp-browser│──┼──────────────┼─▶│  lp-browser serve │  │
│  │ (client)  │  │   + Auth     │  │  (Playwright)     │  │
│  └───────────┘  │              │  └───────────────────┘  │
└─────────────────┘              └─────────────────────────┘
```

**Protocol:**

```python
# Client -> Server
{
    "id": "req_123",
    "method": "navigate",
    "params": {"url": "https://example.com"}
}

# Server -> Client
{
    "id": "req_123",
    "result": {"status": "ok", "title": "Example Domain"}
}

# Server -> Client (event)
{
    "event": "console",
    "params": {"type": "log", "text": "Hello world"}
}
```

**Security:**
- Token-based authentication
- TLS encryption (wss://)
- Rate limiting
- IP whitelist (optional)

---

## lp-notify

**Source:** Uses system `notify-send` (Linux) / `osascript` (macOS)

Desktop notifications.

### CLI

```bash
lp-notify "Message"                       # Simple notification
lp-notify "Message" --title "Title"       # With title
lp-notify "Message" --urgency critical    # Urgent
lp-notify "Message" --icon /path/icon.png # With icon
```

### Implementation

```python
import subprocess
import platform

def notify(message: str, title: str = "🦞 Lobster Powers", urgency: str = "normal"):
    system = platform.system()

    if system == "Linux":
        subprocess.run([
            "notify-send",
            "--urgency", urgency,
            title,
            message
        ])

    elif system == "Darwin":  # macOS
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script])

    elif system == "Windows":
        # Use win10toast or similar
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(title, message)
```

---

## Configuration

### Config File

`~/.config/lobster-powers/config.json`:

```json
{
  "openai": {
    "api_key": "sk-...",
    "organization": "org-..."
  },
  "anthropic": {
    "api_key": "sk-ant-..."
  },
  "elevenlabs": {
    "api_key": "..."
  },
  "brave": {
    "api_key": "..."
  },
  "perplexity": {
    "api_key": "pplx-..."
  },
  "firecrawl": {
    "api_key": "..."
  },
  "tts": {
    "provider": "edge",
    "max_length": 1500,
    "summarize": true
  },
  "memory": {
    "model": "text-embedding-3-small",
    "extra_paths": ["~/notes/"]
  }
}
```

### Environment Variables

All API keys can also be set via environment:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export ELEVENLABS_API_KEY="..."
export BRAVE_API_KEY="..."
export PERPLEXITY_API_KEY="pplx-..."
export FIRECRAWL_API_KEY="..."
```

### CLI Config

```bash
lp-config set openai.api_key "sk-..."     # Set value
lp-config get openai.api_key              # Get value
lp-config list                            # List all settings
lp-config edit                            # Open in $EDITOR
```

---

## Installation

### PyPI

```bash
pip install lobster-powers           # Core only
pip install lobster-powers[all]      # All features
pip install lobster-powers[tts]      # Just TTS
```

### From Source

```bash
git clone https://github.com/superbereza/lobster-powers
cd lobster-powers
pip install -e ".[all]"
```

### System Dependencies

```bash
# Linux
sudo apt install at libnotify-bin

# macOS (at is built-in)
brew install terminal-notifier

# Playwright browsers
playwright install chromium
```

---

## Appendix: OpenClaw Mapping

| OpenClaw Tool | lobster-powers CLI | Notes |
|---------------|-------------------|-------|
| `cron` | `lp-cron` | Uses system at/crontab |
| `memory_search` | `lp-memory search` | Same API |
| `memory_get` | `lp-memory read` | Same API |
| `tts` | `lp-tts` | Same providers |
| `image` | `lp-image` | Same providers |
| `web_fetch` | `lp-web-fetch` | Same features |
| `web_search` | `lp-web-search` | Same providers |
| `browser_*` | `lp-browser *` | Playwright-based |
