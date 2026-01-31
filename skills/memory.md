---
name: memory
description: Semantic search and retrieval from memory files
---

# Memory - Long-term Knowledge

Use `memory_search` and `memory_get` MCP tools to access stored knowledge.

## When to Use

**Always search memory before answering about:**
- Previous decisions and discussions
- Dates, timelines, deadlines
- People, contacts, preferences
- TODOs and task history
- Project context and history

## Tools

### memory_search

Semantic search across all memory files.

```json
{
  "query": "what authentication method did we choose",
  "maxResults": 5
}
```

Returns snippets with file paths and line numbers.

### memory_get

Read specific lines from a memory file.

```json
{
  "path": "memory/2024-01-15.md",
  "from": 42,
  "lines": 20
}
```

Use after `memory_search` to get full context.

## Workflow

1. User asks about past decision
2. Call `memory_search` with relevant query
3. Review returned snippets
4. If needed, call `memory_get` for more context
5. Answer based on found information

## Example

User: "What did we decide about the database?"

```json
// Step 1: Search
{"tool": "memory_search", "query": "database decision"}

// Step 2: Get context if needed
{"tool": "memory_get", "path": "memory/2024-01-10.md", "from": 15, "lines": 30}
```

## Tips

- Be specific in search queries
- Use `maxResults: 3-5` to keep context small
- Combine with project MEMORY.md for best results
