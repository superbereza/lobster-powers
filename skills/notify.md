---
name: notify
description: Send desktop notifications using lp-notify CLI
---

# Notify - Desktop Notifications

Use `lp-notify` to send desktop notifications to the user.

## Quick Examples

```bash
# Simple notification
lp-notify "Task completed!"

# With custom title
lp-notify "Build failed" --title "CI/CD"

# Urgent notification
lp-notify "Server down!" --urgency critical
```

## Commands

| Command | Description |
|---------|-------------|
| `lp-notify "message"` | Send notification |
| `lp-notify "msg" --title "Title"` | Custom title |
| `lp-notify "msg" --urgency critical` | Urgent (Linux) |
| `lp-notify "msg" --icon /path/icon.png` | Custom icon (Linux) |

## When to Use

- Task completed notifications
- Reminders (via lp-cron)
- Error alerts
- Status updates

## Platform Support

| Platform | Backend | Features |
|----------|---------|----------|
| Linux | notify-send | title, urgency, icon |
| macOS | osascript | title only |
