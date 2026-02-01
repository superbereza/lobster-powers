#!/usr/bin/env python3
"""
lp-cron: Schedule reminders and recurring tasks.

Uses system `at` for one-time and `crontab` for recurring jobs.

Examples:
    lp-cron add "Check PRs" --at "9:00 tomorrow"
    lp-cron add "Weekly sync" --cron "0 10 * * 1"
    lp-cron list
    lp-cron remove <job-id>
    lp-cron run <job-id>
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

JOBS_FILE = Path.home() / ".local" / "share" / "lobster-powers" / "cron-jobs.json"


def load_jobs() -> dict:
    """Load jobs from storage."""
    if not JOBS_FILE.exists():
        return {"jobs": [], "next_id": 1}
    return json.loads(JOBS_FILE.read_text())


def save_jobs(data: dict) -> None:
    """Save jobs to storage."""
    JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    JOBS_FILE.write_text(json.dumps(data, indent=2))


def cmd_add(args) -> None:
    """Add a new job."""
    data = load_jobs()
    job_id = data["next_id"]
    data["next_id"] += 1

    job = {
        "id": job_id,
        "text": args.text,
        "created": datetime.now().isoformat(),
    }

    if args.at:
        # One-time job using `at`
        job["type"] = "at"
        job["schedule"] = args.at

        # Create notification command
        notify_cmd = f'notify-send "🦞 Reminder" "{args.text}"'

        try:
            proc = subprocess.run(
                ["at", args.at],
                input=notify_cmd,
                text=True,
                capture_output=True,
            )
            if proc.returncode != 0:
                print(f"Error scheduling with at: {proc.stderr}", file=sys.stderr)
                return
            job["at_job_id"] = proc.stderr.split()[1] if proc.stderr else None
        except FileNotFoundError:
            print("Error: 'at' command not found. Install with: sudo apt install at", file=sys.stderr)
            return

    elif args.cron:
        # Recurring job using crontab
        job["type"] = "cron"
        job["schedule"] = args.cron

        notify_cmd = f'notify-send "🦞 Reminder" "{args.text}"'
        cron_line = f'{args.cron} {notify_cmd} # lp-cron-{job_id}'

        # Add to crontab
        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            existing = result.stdout if result.returncode == 0 else ""
            new_crontab = existing.rstrip() + "\n" + cron_line + "\n"
            subprocess.run(["crontab", "-"], input=new_crontab, text=True, check=True)
        except Exception as e:
            print(f"Error adding to crontab: {e}", file=sys.stderr)
            return

    else:
        print("Error: specify --at or --cron", file=sys.stderr)
        return

    data["jobs"].append(job)
    save_jobs(data)
    print(f"Created job #{job_id}: {args.text}")
    print(f"  Schedule: {job['schedule']} ({job['type']})")


def cmd_list(args) -> None:
    """List all jobs."""
    data = load_jobs()

    if not data["jobs"]:
        print("No jobs scheduled.")
        return

    print("Scheduled jobs:")
    for job in data["jobs"]:
        print(f"  #{job['id']} [{job['type']}] {job['text']}")
        print(f"      Schedule: {job['schedule']}")


def cmd_remove(args) -> None:
    """Remove a job."""
    data = load_jobs()
    job = next((j for j in data["jobs"] if j["id"] == args.job_id), None)

    if not job:
        print(f"Job #{args.job_id} not found.", file=sys.stderr)
        return

    if job["type"] == "at" and job.get("at_job_id"):
        subprocess.run(["atrm", str(job["at_job_id"])], capture_output=True)

    elif job["type"] == "cron":
        # Remove from crontab
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
        return

    subprocess.run(["notify-send", "🦞 Reminder", job["text"]])
    print(f"Triggered: {job['text']}")


def main():
    parser = argparse.ArgumentParser(
        description="Schedule reminders and recurring tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # add
    add_parser = subparsers.add_parser("add", help="Add a new job")
    add_parser.add_argument("text", help="Reminder text")
    add_parser.add_argument("--at", help="One-time schedule (e.g., '9:00 tomorrow')")
    add_parser.add_argument("--cron", help="Cron expression (e.g., '0 9 * * *')")
    add_parser.set_defaults(func=cmd_add)

    # list
    list_parser = subparsers.add_parser("list", help="List all jobs")
    list_parser.set_defaults(func=cmd_list)

    # remove
    rm_parser = subparsers.add_parser("remove", help="Remove a job")
    rm_parser.add_argument("job_id", type=int, help="Job ID to remove")
    rm_parser.set_defaults(func=cmd_remove)

    # run
    run_parser = subparsers.add_parser("run", help="Run a job immediately")
    run_parser.add_argument("job_id", type=int, help="Job ID to run")
    run_parser.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
