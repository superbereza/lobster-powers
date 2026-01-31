"""Cron tool - schedule tasks and reminders.

Based on OpenClaw cron-tool.ts
"""

from typing import Any

from mcp.types import Tool

from ..gateway import OpenClawGateway

TOOL_DESCRIPTION = """Manage scheduled tasks and reminders.

ACTIONS:
- status: Check cron scheduler status
- list: List all jobs (use includeDisabled:true to include disabled)
- add: Create job (requires job object)
- update: Modify job (requires jobId + patch object)
- remove: Delete job (requires jobId)
- run: Trigger job immediately (requires jobId)
- runs: Get job run history (requires jobId)

JOB SCHEMA (for add action):
{
  "name": "string (optional)",
  "schedule": { ... },
  "payload": { ... },
  "sessionTarget": "main" | "isolated",
  "enabled": true | false
}

SCHEDULE TYPES:
- "at": One-shot at absolute time
  { "kind": "at", "atMs": <unix-ms-timestamp> }
- "every": Recurring interval
  { "kind": "every", "everyMs": <interval-ms> }
- "cron": Cron expression
  { "kind": "cron", "expr": "<cron-expression>", "tz": "<timezone>" }

PAYLOAD TYPES:
- "systemEvent": Injects text as system event
  { "kind": "systemEvent", "text": "<message>" }
- "agentTurn": Runs agent with message
  { "kind": "agentTurn", "message": "<prompt>" }

EXAMPLES:

Remind tomorrow at 9:00:
{
  "action": "add",
  "job": {
    "schedule": {"kind": "cron", "expr": "0 9 * * *", "tz": "Europe/Moscow"},
    "payload": {"kind": "agentTurn", "message": "Check PRs"},
    "sessionTarget": "isolated"
  }
}

List all jobs:
{"action": "list"}

Remove a job:
{"action": "remove", "jobId": "abc123"}
"""


def get_tool_definition() -> Tool:
    """Get MCP tool definition for cron."""
    return Tool(
        name="cron",
        description=TOOL_DESCRIPTION,
        inputSchema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["status", "list", "add", "update", "remove", "run", "runs"],
                    "description": "Action to perform",
                },
                "job": {
                    "type": "object",
                    "description": "Job definition (for add action)",
                },
                "jobId": {
                    "type": "string",
                    "description": "Job ID (for update/remove/run/runs)",
                },
                "patch": {
                    "type": "object",
                    "description": "Patch object (for update action)",
                },
                "includeDisabled": {
                    "type": "boolean",
                    "description": "Include disabled jobs in list",
                },
            },
            "required": ["action"],
        },
    )


async def execute(gateway: OpenClawGateway, params: dict[str, Any]) -> dict[str, Any]:
    """Execute cron tool via OpenClaw Gateway."""
    action = params.get("action")

    if action == "status":
        return await gateway.call_tool("cron.status", {})

    elif action == "list":
        return await gateway.call_tool(
            "cron.list",
            {"includeDisabled": params.get("includeDisabled", False)},
        )

    elif action == "add":
        job = params.get("job")
        if not job:
            return {"error": "job required for add action"}
        return await gateway.call_tool("cron.add", job)

    elif action == "update":
        job_id = params.get("jobId")
        patch = params.get("patch")
        if not job_id:
            return {"error": "jobId required for update action"}
        if not patch:
            return {"error": "patch required for update action"}
        return await gateway.call_tool("cron.update", {"id": job_id, "patch": patch})

    elif action == "remove":
        job_id = params.get("jobId")
        if not job_id:
            return {"error": "jobId required for remove action"}
        return await gateway.call_tool("cron.remove", {"id": job_id})

    elif action == "run":
        job_id = params.get("jobId")
        if not job_id:
            return {"error": "jobId required for run action"}
        return await gateway.call_tool("cron.run", {"id": job_id})

    elif action == "runs":
        job_id = params.get("jobId")
        if not job_id:
            return {"error": "jobId required for runs action"}
        return await gateway.call_tool("cron.runs", {"id": job_id})

    else:
        return {"error": f"Unknown action: {action}"}
