---
name: memory
description: Semantic search over notes and files using lp-memory CLI
---

# Memory - Long-term Knowledge

Use `lp-memory` to search your notes, documents, and past decisions.

## Quick Examples

```bash
# Search for something
lp-memory search "what auth method did we choose"

# Index files for searching
lp-memory index ~/notes/
lp-memory index ./MEMORY.md

# Read specific lines
lp-memory read notes/2024-01-15.md --from 42 --lines 20
```

## Commands

| Command | Description |
|---------|-------------|
| `lp-memory search "query"` | Semantic search |
| `lp-memory index <path>` | Add files to index |
| `lp-memory read <file>` | Read file content |
| `lp-memory status` | Show index stats |

## When to Use

**Always search memory before answering about:**
- Previous decisions and discussions
- Dates, timelines, deadlines
- People, contacts, preferences
- TODOs and task history
- Project context and history

## Workflow

1. User asks about past decision
2. Run `lp-memory search "relevant query"`
3. Review returned snippets
4. If needed, `lp-memory read` for full context
5. Answer based on found information

## Tips

- Keep a `MEMORY.md` file in project root with important decisions
- Use `memory/*.md` for dated notes
- Re-index after adding new files
