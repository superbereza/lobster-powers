---
name: cron
description: Schedule tasks and reminders using OpenClaw cron tool
---

# Cron - Task Scheduler

Use the `cron` MCP tool to create scheduled tasks and reminders.

## Quick Examples

### Remind tomorrow at 9:00
```json
{
  "action": "add",
  "job": {
    "schedule": {"kind": "cron", "expr": "0 9 * * *"},
    "payload": {"kind": "agentTurn", "message": "Check pull requests"},
    "sessionTarget": "isolated"
  }
}
```

### Every Monday at 10:00
```json
{
  "action": "add",
  "job": {
    "schedule": {"kind": "cron", "expr": "0 10 * * 1", "tz": "Europe/Moscow"},
    "payload": {"kind": "agentTurn", "message": "Weekly sync reminder"},
    "sessionTarget": "isolated"
  }
}
```

### One-time at specific timestamp
```json
{
  "action": "add",
  "job": {
    "schedule": {"kind": "at", "atMs": 1706857200000},
    "payload": {"kind": "agentTurn", "message": "Meeting starts now!"},
    "sessionTarget": "isolated"
  }
}
```

## Actions

| Action | Description | Required params |
|--------|-------------|-----------------|
| `list` | Show all jobs | - |
| `add` | Create new job | `job` |
| `remove` | Delete job | `jobId` |
| `run` | Execute immediately | `jobId` |
| `status` | Scheduler status | - |

## Schedule Types

### Cron expression
```json
{"kind": "cron", "expr": "0 9 * * *", "tz": "Europe/Moscow"}
```
Standard cron: minute hour day month weekday

### One-time
```json
{"kind": "at", "atMs": 1706857200000}
```
Unix timestamp in milliseconds

### Interval
```json
{"kind": "every", "everyMs": 3600000}
```
Repeat every N milliseconds

## Tips

- Use `sessionTarget: "isolated"` for reminders
- Always specify timezone with `tz` for cron expressions
- Use `list` to see job IDs for removal
