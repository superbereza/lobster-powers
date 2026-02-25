#!/usr/bin/env python3
r"""
lp-cron: Schedule reminders for AI agents.

The agent provides a delivery command that injects the message back into its context.

Examples:
    # Schedule with delivery command
    lp-cron add "Check tests" --in "1h" --deliver "tmux send-keys -t mypane '\$MSG' Enter"

    # List jobs
    lp-cron list

    # Run daemon (checks every 30s)
    lp-cron daemon

    # Single tick (for system cron)
    lp-cron tick
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

JOBS_FILE = Path.home() / ".local" / "share" / "lobster-powers" / "cron-jobs.json"
PID_FILE = Path.home() / ".local" / "share" / "lobster-powers" / "cron-daemon.pid"


def load_jobs() -> dict:
    """Load jobs from storage."""
    if not JOBS_FILE.exists():
        return {"jobs": [], "next_id": 1}
    try:
        return json.loads(JOBS_FILE.read_text())
    except (json.JSONDecodeError, IOError):
        return {"jobs": [], "next_id": 1}


def save_jobs(data: dict) -> None:
    """Save jobs to storage."""
    JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    JOBS_FILE.write_text(json.dumps(data, indent=2))


def parse_duration(duration: str) -> timedelta:
    """Parse duration string like '1h', '30m', '2d', '1h30m'."""
    pattern = r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
    match = re.fullmatch(pattern, duration.strip().lower())

    if not match or not any(match.groups()):
        raise ValueError(f"Invalid duration: {duration}. Use format like '1h', '30m', '2d', '1h30m'")

    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0)
    minutes = int(match.group(3) or 0)
    seconds = int(match.group(4) or 0)

    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


def execute_delivery(job: dict) -> bool:
    """Execute the delivery command for a job."""
    deliver_cmd = job.get("deliver")
    if not deliver_cmd:
        print(f"Job #{job['id']} has no delivery command", file=sys.stderr)
        return False

    # Substitute $MSG with the message
    msg = f"[Reminder] {job['text']}"
    cmd = deliver_cmd.replace("$MSG", msg)

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Delivery failed for job #{job['id']}: {result.stderr}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Delivery error for job #{job['id']}: {e}", file=sys.stderr)
        return False


def cmd_add(args) -> None:
    """Add a new job."""
    if not args.deliver:
        print("Error: --deliver is required. Provide a command to deliver the reminder to you.", file=sys.stderr)
        print("Example: --deliver \"tmux send-keys -t mypane '\\$MSG' Enter\"", file=sys.stderr)
        sys.exit(1)

    try:
        delta = parse_duration(args.duration)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    trigger_at = datetime.now() + delta

    data = load_jobs()
    job_id = data["next_id"]
    data["next_id"] += 1

    job = {
        "id": job_id,
        "text": args.text,
        "deliver": args.deliver,
        "trigger_at": trigger_at.isoformat(),
        "created": datetime.now().isoformat(),
    }

    data["jobs"].append(job)
    save_jobs(data)

    print(f"Scheduled #{job_id}: {args.text}")
    print(f"  Triggers: {trigger_at.strftime('%Y-%m-%d %H:%M:%S')} (in {args.duration})")


def cmd_list(args) -> None:
    """List all jobs."""
    data = load_jobs()

    if not data["jobs"]:
        print("No jobs scheduled.")
        return

    now = datetime.now()
    print("Scheduled jobs:")
    for job in data["jobs"]:
        trigger = datetime.fromisoformat(job["trigger_at"])
        remaining = trigger - now
        if remaining.total_seconds() > 0:
            status = f"in {int(remaining.total_seconds() // 60)}m"
        else:
            status = "pending trigger"

        print(f"  #{job['id']} {job['text']}")
        print(f"      Triggers: {trigger.strftime('%H:%M:%S')} ({status})")


def cmd_remove(args) -> None:
    """Remove a job."""
    data = load_jobs()
    job = next((j for j in data["jobs"] if j["id"] == args.job_id), None)

    if not job:
        print(f"Job #{args.job_id} not found.", file=sys.stderr)
        sys.exit(1)

    data["jobs"] = [j for j in data["jobs"] if j["id"] != args.job_id]
    save_jobs(data)
    print(f"Removed job #{args.job_id}")


def cmd_run(args) -> None:
    """Run a job immediately (for testing)."""
    data = load_jobs()
    job = next((j for j in data["jobs"] if j["id"] == args.job_id), None)

    if not job:
        print(f"Job #{args.job_id} not found.", file=sys.stderr)
        sys.exit(1)

    if execute_delivery(job):
        print(f"Delivered: {job['text']}")
        # Remove one-time job after execution
        data["jobs"] = [j for j in data["jobs"] if j["id"] != args.job_id]
        save_jobs(data)
    else:
        print("Delivery failed", file=sys.stderr)
        sys.exit(1)


def cmd_tick(args) -> None:
    """Check and execute due jobs (single pass)."""
    data = load_jobs()
    now = datetime.now()
    triggered = []

    for job in data["jobs"]:
        trigger_at = datetime.fromisoformat(job["trigger_at"])
        if trigger_at <= now:
            if execute_delivery(job):
                triggered.append(job["id"])
                print(f"Triggered #{job['id']}: {job['text']}")
            else:
                print(f"Failed to deliver #{job['id']}", file=sys.stderr)

    if triggered:
        data["jobs"] = [j for j in data["jobs"] if j["id"] not in triggered]
        save_jobs(data)

    if not triggered and not args.quiet:
        print("No jobs due.")


def cmd_daemon(args) -> None:
    """Run daemon that checks jobs every interval."""
    interval = args.interval

    # Check if already running
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)  # Check if process exists
            print(f"Daemon already running (PID {pid})", file=sys.stderr)
            sys.exit(1)
        except (ProcessLookupError, ValueError):
            pass  # Process doesn't exist, continue

    # Write PID
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))

    print(f"Daemon started (PID {os.getpid()}), checking every {interval}s")

    try:
        while True:
            data = load_jobs()
            now = datetime.now()
            triggered = []

            for job in data["jobs"]:
                trigger_at = datetime.fromisoformat(job["trigger_at"])
                if trigger_at <= now:
                    if execute_delivery(job):
                        triggered.append(job["id"])
                        print(f"[{now.strftime('%H:%M:%S')}] Triggered #{job['id']}: {job['text']}")

            if triggered:
                data["jobs"] = [j for j in data["jobs"] if j["id"] not in triggered]
                save_jobs(data)

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nDaemon stopped")
    finally:
        if PID_FILE.exists():
            PID_FILE.unlink()


def cmd_stop(args) -> None:
    """Stop the daemon."""
    if not PID_FILE.exists():
        print("Daemon not running")
        return

    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 15)  # SIGTERM
        print(f"Stopped daemon (PID {pid})")
        PID_FILE.unlink()
    except ProcessLookupError:
        print("Daemon not running (stale PID file)")
        PID_FILE.unlink()
    except Exception as e:
        print(f"Error stopping daemon: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Schedule reminders for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # add
    add_parser = subparsers.add_parser("add", help="Schedule a reminder")
    add_parser.add_argument("text", help="Reminder text")
    add_parser.add_argument("--in", dest="duration", required=True,
                           help="When to trigger (e.g., '1h', '30m', '2d')")
    add_parser.add_argument("--deliver", required=True,
                           help="Command to deliver reminder ($MSG will be substituted)")
    add_parser.set_defaults(func=cmd_add)

    # list
    list_parser = subparsers.add_parser("list", help="List scheduled jobs")
    list_parser.set_defaults(func=cmd_list)

    # remove
    rm_parser = subparsers.add_parser("remove", help="Remove a job")
    rm_parser.add_argument("job_id", type=int, help="Job ID to remove")
    rm_parser.set_defaults(func=cmd_remove)

    # run (test delivery)
    run_parser = subparsers.add_parser("run", help="Run job immediately (test)")
    run_parser.add_argument("job_id", type=int, help="Job ID to run")
    run_parser.set_defaults(func=cmd_run)

    # tick (single check)
    tick_parser = subparsers.add_parser("tick", help="Check and trigger due jobs")
    tick_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress 'no jobs' message")
    tick_parser.set_defaults(func=cmd_tick)

    # daemon
    daemon_parser = subparsers.add_parser("daemon", help="Run background daemon")
    daemon_parser.add_argument("--interval", type=int, default=30,
                              help="Check interval in seconds (default: 30)")
    daemon_parser.set_defaults(func=cmd_daemon)

    # stop
    stop_parser = subparsers.add_parser("stop", help="Stop the daemon")
    stop_parser.set_defaults(func=cmd_stop)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
