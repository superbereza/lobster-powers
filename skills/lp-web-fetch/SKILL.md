---
name: lp-web-fetch
description: Fetch and extract readable content from URLs using lp-web-fetch
---

# Web Fetch - URL Content Extraction

Use `lp-web-fetch` to fetch web pages and extract readable content.

## Quick Examples

```bash
# Fetch as markdown
lp-web-fetch https://example.com

# Fetch as plain text
lp-web-fetch https://example.com --text

# Limit output size
lp-web-fetch https://example.com --max-chars 5000

# Output as JSON
lp-web-fetch https://example.com --json
```

## Commands

| Option | Description |
|--------|-------------|
| `--text, -t` | Extract as plain text |
| `--max-chars N` | Limit output (default: 50000) |
| `--firecrawl` | Use Firecrawl for JS-heavy pages |
| `--json, -j` | Output as JSON |

## When to Use

- Reading articles and documentation
- Extracting content from web pages
- Research and information gathering
- Before summarizing web content

## Extractors

| Type | Used When |
|------|-----------|
| readability | HTML pages (default) |
| firecrawl | JS-heavy pages (needs API key) |
| json | JSON responses |
| raw | Plain text |
