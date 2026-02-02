---
name: lp-memory
description: Semantic search over notes and files using lp-memory CLI
---

# Memory - Long-term Knowledge

Use `lp-memory` to search your notes, documents, and past decisions.

## Quick Examples

```bash
# Index files
lp-memory index ~/notes/
lp-memory index ./MEMORY.md

# Search
lp-memory search "what auth method did we choose"

# Read specific lines
lp-memory read notes/2024-01-15.md --from 42 --lines 20

# Check status
lp-memory status
```

## Commands

| Command | Description |
|---------|-------------|
| `lp-memory index <path>` | Index file or directory |
| `lp-memory search "query"` | Hybrid search (vector + FTS) |
| `lp-memory read <file>` | Read file content |
| `lp-memory status` | Show index stats |
| `lp-memory forget <path>` | Remove from index |

## Search Options

| Option | Description |
|--------|-------------|
| `--top N` | Return top N results (default: 5) |
| `--vector-weight 0.7` | Weight for vector vs keyword (0-1) |

## When to Use

**Always search memory before answering about:**
- Previous decisions and discussions
- Dates, timelines, deadlines
- People, contacts, preferences
- TODOs and task history
- Project context and history

## How It Works

1. **Index**: Files are split into chunks (~500 chars)
2. **Embed**: Each chunk gets an OpenAI embedding
3. **Search**: Query uses hybrid scoring:
   - 70% vector similarity (semantic)
   - 30% FTS BM25 (keywords)

## Cost

- Model: `text-embedding-3-small` ($0.02/1M tokens)
- Index 100 files: ~$0.01
- 1000 searches: ~$0.10
