# lp-web-fetch Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fetch URLs and extract readable content (HTML → markdown/text).

**Architecture:** HTTP fetch with Readability extraction. Firecrawl as optional fallback for JS-heavy pages.

**Tech Stack:** httpx, readability-lxml, lxml, html2text

---

## Task 1: Create web_fetch.py with Readability extraction

**Files:**
- Create: `src/lobster_powers/tools/web_fetch.py`
- Modify: `pyproject.toml`

**Step 1: Write implementation**

```python
#!/usr/bin/env python3
"""
lp-web-fetch: Fetch and extract readable content from URLs.

Examples:
    lp-web-fetch https://example.com
    lp-web-fetch https://example.com --text
    lp-web-fetch https://example.com --max-chars 5000
"""

import argparse
import json
import os
import sys
from urllib.parse import urlparse

import httpx
from readability import Document
import html2text


DEFAULT_MAX_CHARS = 50000
DEFAULT_TIMEOUT = 30
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def fetch_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> httpx.Response:
    """Fetch URL with proper headers and redirect handling."""
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    return httpx.get(url, headers=headers, follow_redirects=True, timeout=timeout)


def extract_readable(html: str, url: str) -> dict:
    """Extract readable content using Readability."""
    doc = Document(html)
    title = doc.title()
    content_html = doc.summary()

    # Convert to markdown
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0  # No wrapping
    markdown = h.handle(content_html)

    return {
        "title": title,
        "markdown": markdown.strip(),
        "text": h.handle(content_html).strip() if content_html else "",
    }


def fetch_firecrawl(url: str, api_key: str) -> dict:
    """Fetch using Firecrawl API (for JS-heavy pages)."""
    response = httpx.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"url": url, "formats": ["markdown"]},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    if not data.get("success"):
        raise Exception(data.get("error", "Firecrawl failed"))

    return {
        "title": data.get("data", {}).get("metadata", {}).get("title"),
        "markdown": data.get("data", {}).get("markdown", ""),
    }


def truncate(text: str, max_chars: int) -> tuple[str, bool]:
    """Truncate text to max_chars, return (text, was_truncated)."""
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars] + "\n\n[truncated]", True


def web_fetch(
    url: str,
    extract_mode: str = "markdown",
    max_chars: int = DEFAULT_MAX_CHARS,
    use_firecrawl: bool = False,
) -> dict:
    """Fetch URL and extract content."""
    # Validate URL
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL must be http or https")

    firecrawl_key = os.environ.get("FIRECRAWL_API_KEY")

    # Try Firecrawl first if requested
    if use_firecrawl and firecrawl_key:
        try:
            result = fetch_firecrawl(url, firecrawl_key)
            content = result["markdown"]
            if extract_mode == "text":
                h = html2text.HTML2Text()
                h.ignore_links = True
                h.ignore_images = True
                content = h.handle(content)
            content, truncated = truncate(content, max_chars)
            return {
                "url": url,
                "title": result.get("title"),
                "content": content,
                "extractor": "firecrawl",
                "truncated": truncated,
            }
        except Exception as e:
            if not use_firecrawl:
                pass  # Fall through to regular fetch
            else:
                raise

    # Regular fetch
    response = fetch_url(url)
    content_type = response.headers.get("content-type", "")
    final_url = str(response.url)

    if "text/html" in content_type:
        extracted = extract_readable(response.text, final_url)
        content = extracted["markdown"] if extract_mode == "markdown" else extracted["text"]

        # If Readability failed, try Firecrawl as fallback
        if not content.strip() and firecrawl_key:
            try:
                result = fetch_firecrawl(url, firecrawl_key)
                content = result["markdown"]
                if extract_mode == "text":
                    h = html2text.HTML2Text()
                    content = h.handle(content)
                content, truncated = truncate(content, max_chars)
                return {
                    "url": url,
                    "final_url": final_url,
                    "title": result.get("title") or extracted["title"],
                    "content": content,
                    "extractor": "firecrawl",
                    "truncated": truncated,
                }
            except Exception:
                pass  # Return empty content

        content, truncated = truncate(content, max_chars)
        return {
            "url": url,
            "final_url": final_url,
            "title": extracted["title"],
            "content": content,
            "extractor": "readability",
            "truncated": truncated,
        }

    elif "application/json" in content_type:
        try:
            data = response.json()
            content = json.dumps(data, indent=2)
            content, truncated = truncate(content, max_chars)
            return {
                "url": url,
                "final_url": final_url,
                "content": content,
                "extractor": "json",
                "truncated": truncated,
            }
        except Exception:
            pass

    # Plain text or other
    content, truncated = truncate(response.text, max_chars)
    return {
        "url": url,
        "final_url": final_url,
        "content": content,
        "extractor": "raw",
        "truncated": truncated,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and extract readable content from URLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument(
        "--text", "-t",
        action="store_true",
        help="Extract as plain text instead of markdown"
    )
    parser.add_argument(
        "--max-chars", "-m",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help=f"Maximum characters (default: {DEFAULT_MAX_CHARS})"
    )
    parser.add_argument(
        "--firecrawl",
        action="store_true",
        help="Use Firecrawl API (requires FIRECRAWL_API_KEY)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    try:
        result = web_fetch(
            args.url,
            extract_mode="text" if args.text else "markdown",
            max_chars=args.max_chars,
            use_firecrawl=args.firecrawl,
        )

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result.get("title"):
                print(f"# {result['title']}\n")
            print(result["content"])
            if result.get("truncated"):
                print(f"\n[Content truncated at {args.max_chars} chars]", file=sys.stderr)

    except httpx.HTTPStatusError as e:
        print(f"Error: HTTP {e.response.status_code}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 2: Update pyproject.toml**

Add to `[project.scripts]`:
```toml
lp-web-fetch = "lobster_powers.tools.web_fetch:main"
```

Add to `[project.optional-dependencies]`:
```toml
web = ["httpx", "readability-lxml", "lxml", "html2text"]
```

**Step 3: Test manually**

```bash
pip install -e ".[web]"
lp-web-fetch https://example.com
lp-web-fetch https://news.ycombinator.com --max-chars 2000
lp-web-fetch https://api.github.com/repos/anthropics/claude-code --json
```

**Step 4: Commit**

```bash
git add src/lobster_powers/tools/web_fetch.py pyproject.toml
git commit -m "feat(web-fetch): add lp-web-fetch with Readability extraction"
```

---

## Task 2: Create skill file

**Files:**
- Create: `skills/web-fetch.md`

**Step 1: Write skill file**

```markdown
---
name: web-fetch
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
```

**Step 2: Commit**

```bash
git add skills/web-fetch.md
git commit -m "docs(web-fetch): add skill file"
```

---

## Summary

Total: 2 tasks, ~200 lines of code.

Estimated time: 20-30 minutes.
