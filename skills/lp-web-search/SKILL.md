---
name: lp-web-search
description: Web search using lp-web-search with Brave or Perplexity
---

# Web Search

Use `lp-web-search` to search the web.

## Quick Examples

```bash
# Search with auto-detected provider
lp-web-search "python async best practices"

# Use Brave Search
lp-web-search "query" --provider brave --count 10

# Use Perplexity (AI-synthesized)
lp-web-search "explain quantum computing" --provider perplexity

# Filter by freshness (Brave)
lp-web-search "latest news" --freshness pd  # past day
```

## Providers

| Provider | API Key | Output |
|----------|---------|--------|
| brave | `BRAVE_API_KEY` | Traditional search results |
| perplexity | `PERPLEXITY_API_KEY` | AI-synthesized answer with citations |

## Commands

| Option | Description |
|--------|-------------|
| `--provider, -p` | brave or perplexity |
| `--count, -c` | Number of results (Brave, max 10) |
| `--country` | Country code (Brave, e.g., US, DE) |
| `--freshness` | pd=day, pw=week, pm=month, py=year |
| `--json, -j` | Output as JSON |

## When to Use

- Research and information gathering
- Finding documentation
- Current events and news
- Technical questions
