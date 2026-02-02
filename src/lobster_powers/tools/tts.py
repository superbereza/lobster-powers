#!/usr/bin/env python3
"""
lp-tts: Text-to-speech with multiple providers.

Examples:
    lp-tts "Hello world"
    lp-tts "Hello" --provider openai --voice alloy
    lp-tts "Hello" --output speech.mp3
    lp-tts voices
    lp-tts voices --provider edge
"""

import argparse
import asyncio
import os
import sys
import tempfile
from pathlib import Path

from lobster_powers.env import load_env
load_env()

# Provider implementations

async def tts_edge(text: str, voice: str = "en-US-AriaNeural", output: Path | None = None) -> Path:
    """Generate speech using Edge TTS (free, no API key)."""
    try:
        import edge_tts
    except ImportError:
        print("Error: edge-tts not installed. Run: pip install edge-tts", file=sys.stderr)
        sys.exit(1)

    if output is None:
        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        output = Path(path)

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output))
    return output


async def list_edge_voices() -> list[dict]:
    """List available Edge TTS voices."""
    try:
        import edge_tts
    except ImportError:
        return []

    voices = await edge_tts.list_voices()
    return [{"name": v["ShortName"], "gender": v["Gender"], "locale": v["Locale"]} for v in voices]


def tts_openai(text: str, voice: str = "alloy", model: str = "tts-1", output: Path | None = None) -> Path:
    """Generate speech using OpenAI TTS API."""
    try:
        from openai import OpenAI
    except ImportError:
        print("Error: openai not installed. Run: pip install openai", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if output is None:
        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        output = Path(path)

    client = OpenAI(api_key=api_key)
    try:
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format="mp3"
        )
        response.stream_to_file(str(output))
    except Exception as e:
        print(f"Error: OpenAI TTS failed: {e}", file=sys.stderr)
        sys.exit(1)
    return output


def tts_elevenlabs(text: str, voice_id: str = "pMsXgVXv3BLzUgSXRplE", output: Path | None = None) -> Path:
    """Generate speech using ElevenLabs API."""
    try:
        import httpx
    except ImportError:
        print("Error: httpx not installed. Run: pip install httpx", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("Error: ELEVENLABS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if output is None:
        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        output = Path(path)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    try:
        response = httpx.post(
            url,
            headers={"xi-api-key": api_key, "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
            },
            timeout=30.0
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"Error: ElevenLabs API error: {e.response.status_code}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: ElevenLabs TTS failed: {e}", file=sys.stderr)
        sys.exit(1)

    with open(output, "wb") as f:
        f.write(response.content)
    return output


# Provider registry

PROVIDERS = {
    "edge": {"tts": tts_edge, "voices": list_edge_voices, "async": True},
    "openai": {"tts": tts_openai, "voices": None, "async": False},
    "elevenlabs": {"tts": tts_elevenlabs, "voices": None, "async": False},
}

OPENAI_VOICES = ["alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"]


def get_default_provider() -> str:
    """Get default provider based on available API keys."""
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("ELEVENLABS_API_KEY"):
        return "elevenlabs"
    return "edge"


def play_audio(path: Path) -> None:
    """Play audio file using system player."""
    import subprocess
    import platform

    system = platform.system()
    try:
        if system == "Linux":
            # Try common players
            for player in ["mpv", "ffplay", "aplay", "paplay"]:
                try:
                    subprocess.run([player, str(path)], check=True, capture_output=True)
                    return
                except FileNotFoundError:
                    continue
            print(f"Audio saved to: {path}", file=sys.stderr)
        elif system == "Darwin":
            subprocess.run(["afplay", str(path)], check=True)
        else:
            print(f"Audio saved to: {path}")
    except subprocess.CalledProcessError:
        print(f"Audio saved to: {path}")


# CLI commands

def cmd_speak(args) -> None:
    """Generate and optionally play speech."""
    provider = args.provider or get_default_provider()
    output = Path(args.output) if args.output else None

    if provider not in PROVIDERS:
        print(f"Error: unknown provider '{provider}'", file=sys.stderr)
        sys.exit(1)

    prov = PROVIDERS[provider]

    if prov["async"]:
        path = asyncio.run(prov["tts"](args.text, args.voice, output))
    else:
        path = prov["tts"](args.text, args.voice, output)

    if args.output:
        print(f"Saved to: {path}")
    else:
        play_audio(path)
        path.unlink(missing_ok=True)


def cmd_voices(args) -> None:
    """List available voices."""
    provider = args.provider or "edge"

    if provider == "edge":
        voices = asyncio.run(list_edge_voices())
        # Group by locale
        locales = {}
        for v in voices:
            locale = v["locale"]
            if locale not in locales:
                locales[locale] = []
            locales[locale].append(v)

        for locale in sorted(locales.keys()):
            print(f"\n{locale}:")
            for v in locales[locale]:
                print(f"  {v['name']} ({v['gender']})")

    elif provider == "openai":
        print("OpenAI voices:")
        for v in OPENAI_VOICES:
            print(f"  {v}")

    elif provider == "elevenlabs":
        print("ElevenLabs: Use voice IDs from https://elevenlabs.io/voice-library")

    else:
        print(f"Error: unknown provider '{provider}'", file=sys.stderr)
        sys.exit(1)


def main():
    # Check for "voices" subcommand first (before argparse)
    if len(sys.argv) > 1 and sys.argv[1] == "voices":
        parser = argparse.ArgumentParser(description="List available TTS voices")
        parser.add_argument("--provider", "-p", choices=list(PROVIDERS.keys()), help="TTS provider")
        # Skip "voices" arg
        args = parser.parse_args(sys.argv[2:])
        cmd_voices(args)
        return

    # Main parser for speak command
    parser = argparse.ArgumentParser(
        description="Text-to-speech with multiple providers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("text", nargs="?", help="Text to speak")
    parser.add_argument("--provider", "-p", choices=list(PROVIDERS.keys()), help="TTS provider")
    parser.add_argument("--voice", "-v", default="en-US-AriaNeural", help="Voice name/ID")
    parser.add_argument("--output", "-o", help="Output file path")

    args = parser.parse_args()

    if args.text:
        cmd_speak(args)
    else:
        parser.print_help()
        print("\nSubcommands:")
        print("  voices    List available voices")
        sys.exit(1)


if __name__ == "__main__":
    main()
