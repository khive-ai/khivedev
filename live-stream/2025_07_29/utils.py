import os
from pathlib import Path
from typing import Any, List, Literal

from dotenv import load_dotenv
from lionagi import BaseModel, Branch, Session, iModel
from lionagi.fields import Instruct
from lionagi.models import FieldModel
from lionagi.utils import create_path

load_dotenv()

# Configuration
REPO = os.getenv("LOCAL_REPO")
CC_WORKSPACE = os.getenv("CC_WORKSPACE", ".khive/workspaces")


AgentRole = Literal[
    "orchestrator",
    "analyst",
    "architect",
    "auditor",
    "commentator",
    "critic",
    "implementer",
    "innovator",
    "researcher",
    "reviewer",
    "strategist",
    "tester",
    "theorist",
]


class TaskAgentRequest(BaseModel):
    instruct: Instruct
    compose_request: ComposerRequest


class OrchestrationPlan(BaseModel):
    """Plan for orchestrating agent tasks.

    You need to run `uv run khive plan [context]` to gather planners' consensus on agent distribution, and compositions. Each plan is meant for parallel execution, if more rounds
    are needed, you may output the `orchestration_plans` as a list of `OrchestrationPlan` objects.
    """

    common_background: str  # Shared context for all agents
    agent_requests: List[TaskAgentRequest]


def create_cc(
    flow_name: str,
    role: AgentRole,
    agent_suffix: str = "",
    model: str = "sonnet",
    verbose_output: bool = True,
    auto_finish: bool = False,
):
    """Create Claude Code model instance for LionAGI operations."""

    params = {"permission_mode": "acceptEdits"}
    if role == "orchestrator":
        params["permission_mode"] = "bypassPermissions"

    elif role not in ["tester", "reviewer", "architect", "implementer"]:
        params["ws"] = f"{CC_WORKSPACE}/{flow_name}/{role}{agent_suffix}"
        params["add_dir"] = "../../../../"
        text = Path(
            f"{REPO}/{CC_WORKSPACE}/agents/{role}/.claude/settings.json"
        ).read_text()
        fp = create_path(
            directory=f"{REPO}/{CC_WORKSPACE}/{flow_name}/{role}{agent_suffix}/.claude",
            filename="settings.json",
            file_exist_ok=True,
        )
        fp.write_text(text)

        text = Path(
            f"{REPO}/{CC_WORKSPACE}/agents/{role}/.claude/.mcp.json"
        ).read_text()
        fp = create_path(
            directory=f"{REPO}/{CC_WORKSPACE}/{flow_name}/{role}{agent_suffix}",
            filename=".mcp.json",
            file_exist_ok=True,
        )
        fp.write_text(text)

    return iModel(
        provider="claude_code",
        endpoint="query_cli",
        model=model,
        api_key="dummy_api_key",
        verbose_output=verbose_output,
        cli_display_theme="dark",
        auto_finish=auto_finish,
        repo=REPO,
        **params,
    )


async def create_cc_branch(
    compose_request: ComposerRequest,
    flow_name: str,
    agent_suffix: str = "",
    model: str = "sonnet",
    verbose_output: bool = True,
    auto_finish: bool = False,
    clone_from: str = None,
    session: Session = None,
):
    """Create LionAGI branch with khive composer integration."""
    role = compose_request.role
    cc = create_cc(
        role=role,
        flow_name=flow_name,
        agent_suffix=agent_suffix,
        model=model,
        verbose_output=verbose_output,
        auto_finish=auto_finish,
    )

    compose_response: ComposerResponse = await composor.handle_request(
        request=compose_request
    )

    if clone_from:
        if session is None:
            raise ValueError("Session must be provided when clone_from is specified.")
        _from = session.get_branch(clone_from)
        _new = _from.clone(sender=session)
        _new.chat_model = cc
        _new.parse_model = cc
        _new.name = f"{flow_name}_{role}_{compose_request.domains}{agent_suffix}"
        session.branches.include(_new)
        return _new

    branch = Branch(
        chat_model=cc,
        parse_model=cc,
        system=compose_response.system_prompt,
        use_lion_system_message=True,
        system_datetime=True,
        name=f"{flow_name}_{role}_{compose_request.domains}{agent_suffix}",
    )
    if session:
        session.branches.include(branch)
    return branch


# Field models for structured outputs
InstructField = FieldModel(
    base_type=Instruct,
    name="instruct_models",
)

OrchestrationPlanField = FieldModel(
    base_type=OrchestrationPlan,
    name="orchestration_plans",
)


def extract_tool_use_summary(claude_session_response) -> dict[str, Any]:
    """Extract tool usage summary from Claude Code session response.

    Args:
        claude_session_response: ClaudeSession-like object with tool_uses, tool_results, etc.

    Returns:
        Dictionary with tool usage summary including:
        - tool_counts: Count of each tool used
        - tool_details: Detailed information about tool usage
        - file_operations: Summary of file read/write operations
        - key_actions: High-level summary of what was accomplished
        - result_summary: Final result text
        - usage_stats: Token usage and timing info
    """
    if not claude_session_response:
        return {
            "tool_counts": {},
            "tool_details": [],
            "file_operations": {"reads": [], "writes": [], "edits": []},
            "key_actions": ["No tool usage detected"],
            "result_summary": "",
            "usage_stats": {},
        }

    # Access the materialized views directly
    tool_uses = getattr(claude_session_response, "tool_uses", [])
    result = getattr(claude_session_response, "result", "")
    usage = getattr(claude_session_response, "usage", {})

    tool_counts = {}
    tool_details = []
    file_operations = {"reads": [], "writes": [], "edits": []}
    key_actions = []

    # Process tool uses from the clean materialized view
    for tool_use in tool_uses:
        tool_name = tool_use.get("name", "unknown")
        tool_input = tool_use.get("input", {})
        tool_id = tool_use.get("id", "")

        # Count tool usage
        tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

        # Store detailed info
        tool_details.append({"tool": tool_name, "id": tool_id, "input": tool_input})

        # Categorize file operations and actions
        if tool_name in ["Read", "read"]:
            file_path = tool_input.get("file_path", "unknown")
            file_operations["reads"].append(file_path)
            key_actions.append(f"Read {file_path}")

        elif tool_name in ["Write", "write"]:
            file_path = tool_input.get("file_path", "unknown")
            file_operations["writes"].append(file_path)
            key_actions.append(f"Wrote {file_path}")

        elif tool_name in ["Edit", "edit", "MultiEdit"]:
            file_path = tool_input.get("file_path", "unknown")
            file_operations["edits"].append(file_path)
            key_actions.append(f"Edited {file_path}")

        elif tool_name in ["Bash", "bash"]:
            command = tool_input.get("command", "")
            command_summary = command[:50] + "..." if len(command) > 50 else command
            key_actions.append(f"Ran: {command_summary}")

        elif tool_name in ["Glob", "glob"]:
            pattern = tool_input.get("pattern", "")
            key_actions.append(f"Searched files: {pattern}")

        elif tool_name in ["Grep", "grep"]:
            pattern = tool_input.get("pattern", "")
            key_actions.append(f"Searched content: {pattern}")

        elif tool_name in ["Task", "task"]:
            description = tool_input.get("description", "")
            key_actions.append(f"Spawned task: {description}")

        elif tool_name.startswith("mcp__"):
            # MCP tool usage - extract the operation type
            operation = tool_name.replace("mcp__memory__", "").replace("mcp__", "")
            key_actions.append(f"MCP {operation}")

        elif tool_name == "TodoWrite":
            todos = tool_input.get("todos", [])
            key_actions.append(f"Created {len(todos)} todos")

        else:
            key_actions.append(f"Used {tool_name}")

    # Deduplicate key actions
    key_actions = (
        list(dict.fromkeys(key_actions))
        if key_actions
        else ["No specific actions detected"]
    )

    # Deduplicate file paths
    for op_type in file_operations:
        file_operations[op_type] = list(dict.fromkeys(file_operations[op_type]))

    # Extract result summary (first 200 chars)
    result_summary = (result[:200] + "...") if len(result) > 200 else result

    return {
        "tool_counts": tool_counts,
        "tool_details": tool_details,
        "file_operations": file_operations,
        "key_actions": key_actions,
        "total_tool_calls": sum(tool_counts.values()),
        "result_summary": result_summary,
        "usage_stats": {
            "total_cost_usd": getattr(claude_session_response, "total_cost_usd", None),
            "num_turns": getattr(claude_session_response, "num_turns", None),
            "duration_ms": getattr(claude_session_response, "duration_ms", None),
            **usage,
        },
    }


def get_branch_summary_from_operation(session, operation_id, graph) -> dict[str, Any]:
    """Helper to get tool summary directly from an operation's branch.

    Args:
        session: LionAGI session
        operation: Operation object with branch_id

    Returns:
        Tool usage summary dict
    """
    try:
        operation = graph.internal_nodes[operation_id]
        branch = session.get_branch(operation.branch_id, None)
        if branch and hasattr(branch, "messages") and branch.messages:
            # Get the last assistant message which should have the ClaudeSession response
            last_message = branch.messages[-1]
            if hasattr(last_message, "model_response"):
                return {
                    "branch_id": str(branch.id),
                    "branch_name": branch.name,
                    "summary": extract_tool_use_summary(last_message.model_response),
                }
            else:
                return {"error": "No model_response in last message"}
        else:
            return {"error": "No branch or messages found"}
    except Exception as e:
        return {"error": f"Failed to extract summary: {str(e)}"}
