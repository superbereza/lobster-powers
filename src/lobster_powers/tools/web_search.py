#!/usr/bin/env python3
"""
lp-web-search: Web search with Brave and Perplexity.

Examples:
    lp-web-search "python async tutorial"
    lp-web-search "query" --provider brave --count 10
    lp-web-search "query" --provider perplexity
"""

import argparse
import json
import os
import sys

import httpx


DEFAULT_COUNT = 5
MAX_COUNT = 10
DEFAULT_TIMEOUT = 30

BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
PERPLEXITY_ENDPOINT = "https://api.perplexity.ai/chat/completions"
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


def search_brave(
    query: str,
    api_key: str,
    count: int = DEFAULT_COUNT,
    country: str | None = None,
    freshness: str | None = None,
) -> dict:
    """Search using Brave Search API."""
    params = {"q": query, "count": min(count, MAX_COUNT)}
    if country:
        params["country"] = country
    if freshness:
        params["freshness"] = freshness

    response = httpx.get(
        BRAVE_ENDPOINT,
        params=params,
        headers={
            "Accept": "application/json",
            "X-Subscription-Token": api_key,
        },
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()

    results = []
    for r in data.get("web", {}).get("results", []):
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "description": r.get("description", ""),
        })

    return {
        "provider": "brave",
        "query": query,
        "count": len(results),
        "results": results,
    }


def search_perplexity(query: str, api_key: str) -> dict:
    """Search using Perplexity Sonar API."""
    # Detect if using OpenRouter or direct Perplexity
    if api_key.startswith("sk-or-"):
        endpoint = OPENROUTER_ENDPOINT
        model = "perplexity/sonar-pro"
    else:
        endpoint = PERPLEXITY_ENDPOINT
        model = "sonar-pro"

    response = httpx.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": query}],
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    citations = data.get("citations", [])

    return {
        "provider": "perplexity",
        "query": query,
        "content": content,
        "citations": citations,
    }


def get_provider_and_key() -> tuple[str, str]:
    """Detect available provider and API key."""
    brave_key = os.environ.get("BRAVE_API_KEY")
    perplexity_key = os.environ.get("PERPLEXITY_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")

    if brave_key:
        return "brave", brave_key
    if perplexity_key:
        return "perplexity", perplexity_key
    if openrouter_key:
        return "perplexity", openrouter_key

    return "", ""


def format_brave_results(data: dict) -> str:
    """Format Brave results for display."""
    lines = [f"Search: {data['query']}", f"Found {data['count']} results:", ""]
    for i, r in enumerate(data["results"], 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   {r['url']}")
        if r["description"]:
            lines.append(f"   {r['description'][:200]}")
        lines.append("")
    return "\n".join(lines)


def format_perplexity_results(data: dict) -> str:
    """Format Perplexity results for display."""
    lines = [data["content"], ""]
    if data["citations"]:
        lines.append("Sources:")
        for i, url in enumerate(data["citations"], 1):
            lines.append(f"  [{i}] {url}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Web search with Brave and Perplexity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--provider", "-p",
        choices=["brave", "perplexity"],
        help="Search provider (auto-detected by default)"
    )
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=DEFAULT_COUNT,
        help=f"Number of results (Brave only, default: {DEFAULT_COUNT})"
    )
    parser.add_argument(
        "--country",
        help="Country code for regional results (Brave only, e.g., US, DE)"
    )
    parser.add_argument(
        "--freshness",
        choices=["pd", "pw", "pm", "py"],
        help="Freshness filter: pd=day, pw=week, pm=month, py=year (Brave only)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    # Get provider
    default_provider, default_key = get_provider_and_key()
    provider = args.provider or default_provider

    if not provider:
        print("Error: No API key found. Set BRAVE_API_KEY or PERPLEXITY_API_KEY", file=sys.stderr)
        sys.exit(1)

    # Get API key for selected provider
    if provider == "brave":
        api_key = os.environ.get("BRAVE_API_KEY")
        if not api_key:
            print("Error: BRAVE_API_KEY not set", file=sys.stderr)
            sys.exit(1)
    else:
        api_key = os.environ.get("PERPLEXITY_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print("Error: PERPLEXITY_API_KEY or OPENROUTER_API_KEY not set", file=sys.stderr)
            sys.exit(1)

    try:
        if provider == "brave":
            result = search_brave(
                args.query,
                api_key,
                count=args.count,
                country=args.country,
                freshness=args.freshness,
            )
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(format_brave_results(result))
        else:
            result = search_perplexity(args.query, api_key)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(format_perplexity_results(result))

    except httpx.HTTPStatusError as e:
        print(f"Error: HTTP {e.response.status_code}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
