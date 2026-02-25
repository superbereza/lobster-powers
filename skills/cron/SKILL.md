---
name: cron
description: Schedule reminders that come back to you (the agent)
---

# Cron - Reminders for Agents

Schedule a reminder that will be delivered back to YOU (the agent), not the user.

## How it works

1. You figure out HOW to receive the reminder (you know your environment)
2. You pass that as `--deliver` command
3. When time comes, your command executes with `$MSG` substituted
4. You receive the reminder as input and decide what to do

## Quick Start

```bash
# 1. Figure out your delivery method (see below)
# 2. Schedule reminder
lp-cron add "Check test results" --in "1h" --deliver "YOUR_DELIVERY_COMMAND"

# 3. Make sure daemon is running
lp-cron daemon &
```

## Your Job: Figure Out Delivery

You need to provide a command that injects `$MSG` into YOUR input/context.

**Think about your environment:**

### If you're in tmux (most common)
```bash
# Find your pane
tmux display-message -p '#{session_name}:#{window_index}.#{pane_index}'
# Example output: claude-codogram-myproject:0.0

# Use it
lp-cron add "Check tests" --in "1h" \
  --deliver "tmux send-keys -t claude-codogram-myproject:0.0 '\$MSG' Enter"
```

### If you have a Claude session file
```bash
lp-cron add "Review PR" --in "2h" \
  --deliver "claude --resume SESSION_ID -p '\$MSG'"
```

### Other environments
Figure out how to inject text into your stdin/context and use that command.

## Commands

| Command | Description |
|---------|-------------|
| `lp-cron add TEXT --in TIME --deliver CMD` | Schedule reminder |
| `lp-cron list` | Show scheduled jobs |
| `lp-cron remove ID` | Cancel a job |
| `lp-cron run ID` | Trigger immediately (test) |
| `lp-cron tick` | Check and trigger due jobs (one pass) |
| `lp-cron daemon` | Run background checker |
| `lp-cron stop` | Stop daemon |

## Time Format (--in)

- `30s` - 30 seconds
- `5m` - 5 minutes
- `1h` - 1 hour
- `2d` - 2 days
- `1h30m` - 1 hour 30 minutes

## Running the Scheduler

Jobs only trigger when the scheduler runs. Options:

```bash
# Option 1: Daemon (recommended)
lp-cron daemon &

# Option 2: System cron (add to crontab -e)
* * * * * /path/to/lp-cron tick -q

# Option 3: Manual check
lp-cron tick
```

## Example Flow

```bash
# You want a reminder in 1 hour
PANE=$(tmux display-message -p '#{session_name}:#{window_index}.#{pane_index}')
lp-cron add "Time to check if tests passed" --in "1h" \
  --deliver "tmux send-keys -t $PANE '\$MSG' Enter"

# Make sure daemon is running
lp-cron daemon &

# ... 1 hour later ...
# You receive: [Reminder] Time to check if tests passed
# Now you decide: check tests, respond to user, or ignore
```
