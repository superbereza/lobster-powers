#!/usr/bin/env python3
"""
lp-image: Analyze images using vision models.

Examples:
    lp-image photo.jpg
    lp-image photo.jpg "What objects are in this image?"
    lp-image https://example.com/image.png "Describe this"
    lp-image photo.jpg --provider anthropic
"""

import argparse
import base64
import mimetypes
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx


DEFAULT_PROMPT = "Describe this image in detail."
DEFAULT_MAX_TOKENS = 1024


def load_image_as_base64(source: str) -> tuple[str, str]:
    """
    Load image from file path or URL, return (base64_data, mime_type).
    """
    # Data URL
    if source.startswith("data:"):
        # data:image/png;base64,xxxxx
        header, data = source.split(",", 1)
        mime_type = header.split(";")[0].split(":")[1]
        return data, mime_type

    # URL
    if source.startswith(("http://", "https://")):
        response = httpx.get(source, follow_redirects=True, timeout=30)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "image/png")
        mime_type = content_type.split(";")[0]
        return base64.b64encode(response.content).decode(), mime_type

    # Local file
    path = Path(source).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {source}")

    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type or not mime_type.startswith("image/"):
        mime_type = "image/png"

    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode(), mime_type


def analyze_openai(
    image_base64: str,
    mime_type: str,
    prompt: str,
    api_key: str,
    model: str = "gpt-4o-mini",
) -> str:
    """Analyze image using OpenAI Vision API."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_base64}"
                        },
                    },
                ],
            }
        ],
        max_tokens=DEFAULT_MAX_TOKENS,
    )

    return response.choices[0].message.content


def analyze_anthropic(
    image_base64: str,
    mime_type: str,
    prompt: str,
    api_key: str,
    model: str = "claude-sonnet-4-20250514",
) -> str:
    """Analyze image using Anthropic Vision API."""
    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model,
        max_tokens=DEFAULT_MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": image_base64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    return response.content[0].text


def get_provider_and_key() -> tuple[str, str]:
    """Detect available provider and API key."""
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    if openai_key:
        return "openai", openai_key
    if anthropic_key:
        return "anthropic", anthropic_key

    return "", ""


def main():
    parser = argparse.ArgumentParser(
        description="Analyze images using vision models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("image", help="Image file path or URL")
    parser.add_argument("prompt", nargs="?", default=DEFAULT_PROMPT, help="Prompt/question about the image")
    parser.add_argument(
        "--provider", "-p",
        choices=["openai", "anthropic"],
        help="Vision provider (auto-detected by default)"
    )
    parser.add_argument(
        "--model", "-m",
        help="Model to use (default: gpt-4o-mini or claude-sonnet-4)"
    )

    args = parser.parse_args()

    # Get provider
    default_provider, default_key = get_provider_and_key()
    provider = args.provider or default_provider

    if not provider:
        print("Error: No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY", file=sys.stderr)
        sys.exit(1)

    # Get API key
    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("Error: OPENAI_API_KEY not set", file=sys.stderr)
            sys.exit(1)
        model = args.model or "gpt-4o-mini"
    else:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not set", file=sys.stderr)
            sys.exit(1)
        model = args.model or "claude-sonnet-4-20250514"

    try:
        # Load image
        image_base64, mime_type = load_image_as_base64(args.image)

        # Analyze
        if provider == "openai":
            result = analyze_openai(image_base64, mime_type, args.prompt, api_key, model)
        else:
            result = analyze_anthropic(image_base64, mime_type, args.prompt, api_key, model)

        print(result)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
