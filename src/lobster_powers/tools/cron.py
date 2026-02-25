#!/usr/bin/env python3
"""
lp-cron: Schedule reminders for AI agents using system at/cron.

Thin wrapper over system `at` (one-time) and `crontab` (recurring).
The agent provides a delivery command that injects the message back into its context.

Examples:
    # One-time (uses `at`)
    lp-cron add "Check tests" --in "1h" --deliver "tmux send-keys -t pane '\$MSG' Enter"

    # Recurring (uses crontab)
    lp-cron add "Daily standup" --cron "0 10 * * *" --deliver "tmux send-keys -t pane '\$MSG' Enter"

    # List all jobs
    lp-cron list

    # Remove a job
    lp-cron remove <id>

Requirements:
    - `at` package for one-time jobs: sudo apt install at
    - `cron` for recurring jobs (usually pre-installed)
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

JOBS_FILE = Path.home() / ".local" / "share" / "lobster-powers" / "cron-jobs.json"


def load_jobs() -> dict:
    """Load jobs metadata from storage."""
    if not JOBS_FILE.exists():
        return {"jobs": [], "next_id": 1}
    try:
        return json.loads(JOBS_FILE.read_text())
    except (json.JSONDecodeError, IOError):
        return {"jobs": [], "next_id": 1}


def save_jobs(data: dict) -> None:
    """Save jobs metadata to storage."""
    JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    JOBS_FILE.write_text(json.dumps(data, indent=2))


def parse_duration_to_at(duration: str) -> str:
    """Convert duration like '1h', '30m', '2d' to `at` format."""
    pattern = r'^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$'
    match = re.fullmatch(pattern, duration.strip().lower())

    if not match or not any(match.groups()):
        raise ValueError(f"Invalid duration: {duration}. Use format like '1h', '30m', '2d', '1h30m'")

    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0)
    minutes = int(match.group(3) or 0)
    seconds = int(match.group(4) or 0)

    # Convert to minutes for `at` (it doesn't do seconds well)
    total_minutes = days * 24 * 60 + hours * 60 + minutes + (1 if seconds > 0 else 0)

    if total_minutes < 1:
        total_minutes = 1

    return f"now + {total_minutes} minutes"


def build_delivery_command(deliver: str, message: str) -> str:
    """Build the delivery command with $MSG substituted."""
    reminder_text = f"[Reminder] {message}"
    return deliver.replace("$MSG", reminder_text)


def cmd_add(args) -> None:
    """Add a new job."""
    if not args.deliver:
        print("Error: --deliver is required.", file=sys.stderr)
        print('Example: --deliver "tmux send-keys -t mypane \'\\$MSG\' Enter"', file=sys.stderr)
        sys.exit(1)

    if not args.duration and not args.cron:
        print("Error: specify --in or --cron", file=sys.stderr)
        sys.exit(1)

    data = load_jobs()
    job_id = data["next_id"]
    data["next_id"] += 1

    delivery_cmd = build_delivery_command(args.deliver, args.text)

    job = {
        "id": job_id,
        "text": args.text,
        "deliver": args.deliver,
    }

    if args.duration:
        # One-time job using `at`
        try:
            at_time = parse_duration_to_at(args.duration)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        try:
            # at_time is like "now + 5 minutes"
            proc = subprocess.run(
                f"at -M {at_time}",
                shell=True,
                input=delivery_cmd,
                text=True,
                capture_output=True,
            )
            if proc.returncode != 0:
                print(f"Error scheduling with at: {proc.stderr}", file=sys.stderr)
                sys.exit(1)

            # Parse at job ID from stderr (format: "job N at ...")
            at_output = proc.stderr.strip()
            at_job_match = re.search(r'job (\d+)', at_output)
            if at_job_match:
                job["at_job_id"] = at_job_match.group(1)

            job["type"] = "at"
            job["schedule"] = args.duration

        except FileNotFoundError:
            print("Error: 'at' command not found.", file=sys.stderr)
            print("Install with: sudo apt install at", file=sys.stderr)
            print("Then start the service: sudo systemctl enable --now atd", file=sys.stderr)
            sys.exit(1)

    elif args.cron:
        # Recurring job using crontab
        job["type"] = "cron"
        job["schedule"] = args.cron

        cron_line = f'{args.cron} {delivery_cmd} # lp-cron-{job_id}'

        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            existing = result.stdout if result.returncode == 0 else ""
            new_crontab = existing.rstrip() + "\n" + cron_line + "\n"

            proc = subprocess.run(["crontab", "-"], input=new_crontab, text=True, capture_output=True)
            if proc.returncode != 0:
                print(f"Error adding to crontab: {proc.stderr}", file=sys.stderr)
                sys.exit(1)

        except Exception as e:
            print(f"Error adding to crontab: {e}", file=sys.stderr)
            sys.exit(1)

    data["jobs"].append(job)
    save_jobs(data)

    print(f"Scheduled #{job_id}: {args.text}")
    print(f"  Type: {job['type']}, Schedule: {job['schedule']}")


def cmd_list(args) -> None:
    """List all jobs."""
    data = load_jobs()

    if not data["jobs"]:
        print("No jobs scheduled.")
        return

    print("Scheduled jobs:")
    for job in data["jobs"]:
        job_type = job.get("type", "unknown")
        schedule = job.get("schedule", "?")
        at_id = job.get("at_job_id", "")
        at_info = f" (at job {at_id})" if at_id else ""

        print(f"  #{job['id']} [{job_type}] {job['text']}")
        print(f"      Schedule: {schedule}{at_info}")


def cmd_remove(args) -> None:
    """Remove a job."""
    data = load_jobs()
    job = next((j for j in data["jobs"] if j["id"] == args.job_id), None)

    if not job:
        print(f"Job #{args.job_id} not found.", file=sys.stderr)
        sys.exit(1)

    # Remove from system
    if job.get("type") == "at" and job.get("at_job_id"):
        subprocess.run(["atrm", str(job["at_job_id"])], capture_output=True)

    elif job.get("type") == "cron":
        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            if result.returncode == 0:
                marker = f"# lp-cron-{job['id']}"
                lines = [l for l in result.stdout.splitlines() if marker not in l]
                subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True)
        except Exception:
            pass

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

    delivery_cmd = build_delivery_command(job["deliver"], job["text"])

    result = subprocess.run(delivery_cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Delivered: {job['text']}")
    else:
        print(f"Delivery failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Schedule reminders for AI agents (uses system at/cron)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # add
    add_parser = subparsers.add_parser("add", help="Schedule a reminder")
    add_parser.add_argument("text", help="Reminder text")
    add_parser.add_argument("--in", dest="duration", help="One-time delay (e.g., '1h', '30m', '2d')")
    add_parser.add_argument("--cron", help="Recurring cron expression (e.g., '0 9 * * *')")
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

    # run (test)
    run_parser = subparsers.add_parser("run", help="Run job immediately (test)")
    run_parser.add_argument("job_id", type=int, help="Job ID to run")
    run_parser.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
