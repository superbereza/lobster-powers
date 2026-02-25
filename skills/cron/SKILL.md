---
name: cron
description: Schedule reminders that come back to you (the agent)
---

# Cron - Reminders for Agents

Schedule a reminder that will be delivered back to YOU (the agent), not the user.

## How it works

1. You figure out HOW to receive the reminder (you know your environment)
2. You pass that as `--deliver` command
3. System `at` (one-time) or `crontab` (recurring) executes your command
4. You receive the reminder as input and decide what to do

## Usage

```bash
# One-time (uses system `at`)
lp-cron add "Check test results" --in "1h" --deliver "YOUR_COMMAND"

# Recurring (uses system crontab)
lp-cron add "Daily standup" --cron "0 10 * * *" --deliver "YOUR_COMMAND"
```

## Your Job: Figure Out Delivery

Provide a command that injects `$MSG` into YOUR input/context.

### If you're in tmux (most common)

```bash
# Find your pane
PANE=$(tmux display-message -p '#{session_name}:#{window_index}.#{pane_index}')

# Use this delivery command (sleep 1 is important!)
lp-cron add "Check tests" --in "1h" \
  --deliver "tmux send-keys -t $PANE '\$MSG' && sleep 1 && tmux send-keys -t $PANE Enter"
```

**Important:** The `sleep 1` before Enter is critical for reliable delivery.

### Other environments

Figure out how to inject text into your stdin/context and use that command.

## Commands

| Command | Description |
|---------|-------------|
| `lp-cron add TEXT --in TIME --deliver CMD` | One-time reminder |
| `lp-cron add TEXT --cron EXPR --deliver CMD` | Recurring reminder |
| `lp-cron list` | Show scheduled jobs |
| `lp-cron remove ID` | Cancel a job |
| `lp-cron run ID` | Trigger immediately (test) |

## Time Formats

**--in (one-time):**
- `5m` - 5 minutes
- `1h` - 1 hour
- `2d` - 2 days
- `1h30m` - 1 hour 30 minutes

**--cron (recurring):**
- `0 9 * * *` - every day at 9am
- `0 10 * * 1` - every Monday at 10am
- `*/15 * * * *` - every 15 minutes

## Requirements

- `at` for one-time: `sudo apt install at && sudo systemctl enable --now atd`
- `cron` for recurring (usually pre-installed)

## Example Flow

```bash
# You want a reminder in 1 hour
PANE=$(tmux display-message -p '#{session_name}:#{window_index}.#{pane_index}')
lp-cron add "Time to check if tests passed" --in "1h" \
  --deliver "tmux send-keys -t $PANE '\$MSG' && sleep 1 && tmux send-keys -t $PANE Enter"

# ... 1 hour later ...
# You receive: [Reminder] Time to check if tests passed
# Now you decide: check tests, respond to user, or ignore
```
