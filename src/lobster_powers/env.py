"""Load .env from lobster-powers repo root."""

from pathlib import Path

def load_env():
    """Load .env file from repo root (where pyproject.toml is)."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return  # dotenv not installed, skip

    # Find repo root by looking for pyproject.toml
    current = Path(__file__).resolve().parent
    for _ in range(5):  # Max 5 levels up
        if (current / "pyproject.toml").exists():
            env_file = current / ".env"
            if env_file.exists():
                load_dotenv(env_file)
            return
        current = current.parent
