---
name: tts
description: Text-to-speech using lp-tts CLI with Edge/OpenAI/ElevenLabs
---

# TTS - Text to Speech

Use `lp-tts` to convert text to speech.

## Quick Examples

```bash
# Speak with default provider (Edge TTS, free)
lp-tts "Hello world"

# Use specific provider
lp-tts "Hello" --provider openai --voice alloy

# Save to file
lp-tts "Hello" --output greeting.mp3

# List voices
lp-tts voices --provider edge
```

## Providers

| Provider | API Key | Cost | Voices |
|----------|---------|------|--------|
| **edge** (default) | None | Free | 300+ Microsoft voices |
| openai | `OPENAI_API_KEY` | $15/1M chars | alloy, ash, coral, echo, fable, onyx, nova, sage, shimmer |
| elevenlabs | `ELEVENLABS_API_KEY` | $0.30/1K chars | Custom voice clones |

## Commands

| Command | Description |
|---------|-------------|
| `lp-tts "text"` | Speak text |
| `lp-tts "text" --provider openai` | Use OpenAI |
| `lp-tts "text" --voice alloy` | Specific voice |
| `lp-tts "text" --output file.mp3` | Save to file |
| `lp-tts voices` | List available voices |

## When to Use

- Reading responses aloud
- Accessibility
- Voice notifications
- Content creation
