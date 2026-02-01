#!/usr/bin/env python3
"""
lp-notify: Desktop notifications.

Examples:
    lp-notify "Hello world"
    lp-notify "Meeting in 5min" --title "Calendar"
    lp-notify "Deploy failed!" --urgency critical
"""

import argparse
import platform
import subprocess
import sys


def notify_linux(message: str, title: str, urgency: str, icon: str | None) -> bool:
    """Send notification via notify-send (Linux)."""
    cmd = ["notify-send"]

    if urgency:
        cmd.extend(["--urgency", urgency])

    if icon:
        cmd.extend(["--icon", icon])

    cmd.append(title)
    cmd.append(message)

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except FileNotFoundError:
        print("Error: notify-send not found. Install with: sudo apt install libnotify-bin", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr.decode() if e.stderr else 'notification failed'}", file=sys.stderr)
        return False


def notify_macos(message: str, title: str, urgency: str, icon: str | None) -> bool:
    """Send notification via osascript (macOS)."""
    # osascript doesn't support urgency or custom icons easily
    script = f'display notification "{message}" with title "{title}"'

    try:
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        return True
    except FileNotFoundError:
        print("Error: osascript not found", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr.decode() if e.stderr else 'notification failed'}", file=sys.stderr)
        return False


def notify(message: str, title: str = "🦞 Lobster Powers", urgency: str = "normal", icon: str | None = None) -> bool:
    """Send desktop notification (cross-platform)."""
    system = platform.system()

    if system == "Linux":
        return notify_linux(message, title, urgency, icon)
    elif system == "Darwin":
        return notify_macos(message, title, urgency, icon)
    else:
        print(f"Error: unsupported platform {system}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Send desktop notifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("message", help="Notification message")
    parser.add_argument("--title", "-t", default="🦞 Lobster Powers", help="Notification title")
    parser.add_argument(
        "--urgency", "-u",
        choices=["low", "normal", "critical"],
        default="normal",
        help="Urgency level (Linux only)"
    )
    parser.add_argument("--icon", "-i", help="Icon path (Linux only)")

    args = parser.parse_args()

    success = notify(args.message, args.title, args.urgency, args.icon)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
