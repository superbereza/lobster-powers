---
name: cron
description: Schedule reminders and recurring tasks using lp-cron CLI
---

# Cron - Task Scheduler

Use `lp-cron` to schedule one-time reminders and recurring tasks.

## Quick Examples

### One-time reminder
```bash
lp-cron add "Check pull requests" --at "9:00 tomorrow"
lp-cron add "Call mom" --at "5pm"
lp-cron add "Meeting starts" --at "now + 30 minutes"
```

### Recurring tasks
```bash
lp-cron add "Daily standup" --cron "0 10 * * *"
lp-cron add "Weekly review" --cron "0 14 * * 5"
lp-cron add "Monthly backup" --cron "0 3 1 * *"
```

## Commands

| Command | Description |
|---------|-------------|
| `lp-cron add "text" --at "time"` | One-time reminder |
| `lp-cron add "text" --cron "expr"` | Recurring task |
| `lp-cron list` | Show all jobs |
| `lp-cron remove <id>` | Delete a job |
| `lp-cron run <id>` | Trigger immediately |

## Time Formats (--at)

Powered by `at` command:
- `9:00` - today at 9am
- `9:00 tomorrow` - tomorrow at 9am
- `now + 30 minutes` - 30 minutes from now
- `5pm friday` - next Friday at 5pm
- `noon` - today at 12pm

## Cron Expressions (--cron)

Standard cron format: `minute hour day month weekday`

| Expression | Meaning |
|------------|---------|
| `0 9 * * *` | Every day at 9am |
| `0 9 * * 1-5` | Weekdays at 9am |
| `0 10 * * 1` | Every Monday at 10am |
| `*/15 * * * *` | Every 15 minutes |
| `0 0 1 * *` | First day of month |

## Tips

- Jobs trigger `notify-send` - ensure desktop notifications work
- Use `lp-cron list` to see all scheduled jobs
- One-time jobs are removed after execution
