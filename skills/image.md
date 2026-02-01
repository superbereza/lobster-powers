---
name: image
description: Analyze images using vision models via lp-image
---

# Image - Vision Analysis

Use `lp-image` to analyze images with AI vision models.

## Quick Examples

```bash
# Describe an image
lp-image photo.jpg

# Ask a specific question
lp-image photo.jpg "What objects are visible?"

# Analyze from URL
lp-image https://example.com/image.png "Describe this"

# Use specific provider
lp-image photo.jpg --provider anthropic
```

## Providers

| Provider | API Key | Models |
|----------|---------|--------|
| openai | `OPENAI_API_KEY` | gpt-4o-mini (default), gpt-4o |
| anthropic | `ANTHROPIC_API_KEY` | claude-sonnet-4 (default) |

## Commands

| Option | Description |
|--------|-------------|
| `--provider, -p` | openai or anthropic |
| `--model, -m` | Specific model to use |

## Supported Formats

- Local files: `photo.jpg`, `~/images/pic.png`
- URLs: `https://example.com/image.png`
- Data URLs: `data:image/png;base64,...`

## When to Use

- Describing image contents
- Extracting text from screenshots
- Analyzing charts and diagrams
- Identifying objects in photos
