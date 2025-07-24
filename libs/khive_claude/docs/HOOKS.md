# Claude Code Hook System Guide

This guide explains how Claude Code's hook system works and how to leverage it for monitoring and automation.

## Overview

Claude Code hooks allow you to intercept and respond to various events during Claude's interaction with your system. This enables:

- Real-time monitoring of all tool usage
- Custom automation and workflows
- Security auditing and compliance
- Performance tracking and optimization

## Hook Types

### 1. UserPromptSubmit

Triggered when a user submits a prompt to Claude.

**Hook Input:**
```json
{
  "prompt": "The user's message",
  "session_id": "unique-session-id",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Use Cases:**
- Track user activity patterns
- Analyze prompt complexity
- Log conversation history

### 2. PreToolUse

Triggered before Claude uses any tool (Bash, Edit, Write, Task, etc.).

**Hook Input:**
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "ls -la",
    "description": "List directory contents"
  },
  "session_id": "unique-session-id"
}
```

**Use Cases:**
- Validate commands before execution
- Implement security policies
- Block dangerous operations

### 3. PostToolUse

Triggered after Claude completes a tool operation.

**Hook Input:**
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "ls -la"
  },
  "tool_output": {
    "output": "total 24\ndrwxr-xr-x  3 user  staff   96 Jan  1 00:00 .\n...",
    "exit_code": 0
  },
  "session_id": "unique-session-id"
}
```

**Use Cases:**
- Log command outputs
- Track execution times
- Monitor error rates

### 4. Notification

Triggered for system notifications and status updates.

**Hook Input:**
```json
{
  "severity": "info",
  "message": "Claude is waiting for your input",
  "timestamp": "2024-01-01T00:00:00Z",
  "session_id": "unique-session-id"
}
```

**Use Cases:**
- System health monitoring
- Error tracking
- User activity alerts

## Hook Configuration

### Basic Structure

Hooks are configured in `.claude/settings.json`:

```json
{
  "HookType": {
    "command": "command to execute"
  }
}
```

### Advanced Configuration with Matchers

For PreToolUse and PostToolUse, you can use matchers to target specific tools:

```json
{
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "python handle_bash.py"
      }]
    },
    {
      "matcher": "Edit|MultiEdit|Write",
      "hooks": [{
        "type": "command",
        "command": "python handle_file_ops.py"
      }]
    }
  ]
}
```

### Matcher Patterns

- **Exact match**: `"Bash"` - matches only Bash tool
- **OR pattern**: `"Edit|Write"` - matches Edit OR Write
- **All tools**: Omit matcher to catch all tools

## Hook Script Development

### Basic Hook Script Structure

```python
#!/usr/bin/env python3
import json
import sys

def main():
    # Read input from stdin
    hook_input = json.load(sys.stdin)
    
    # Process the hook event
    result = process_hook(hook_input)
    
    # Return result to Claude Code
    print(json.dumps(result))
    
    # Exit code determines whether to proceed
    sys.exit(0 if result.get("proceed", True) else 1)

def process_hook(data):
    # Your custom logic here
    tool_name = data.get("tool_name")
    
    # Example: Block dangerous commands
    if tool_name == "Bash":
        command = data.get("tool_input", {}).get("command", "")
        if "rm -rf /" in command:
            return {"proceed": False, "reason": "Dangerous command blocked"}
    
    return {"proceed": True}

if __name__ == "__main__":
    main()
```

### Hook Response Format

Your hook must return a JSON response:

```json
{
  "proceed": true,    // Whether Claude should continue
  "reason": "...",    // Optional: Why blocked
  "metadata": {}      // Optional: Additional data
}
```

### Exit Codes

- `0`: Proceed with the operation
- `1`: Block the operation

## Best Practices

### 1. Performance

- Keep hooks lightweight and fast
- Use async operations for I/O
- Cache frequently accessed data
- Avoid blocking operations

### 2. Error Handling

```python
try:
    # Your hook logic
    result = process_event(data)
except Exception as e:
    # Log error but don't block Claude
    log_error(e)
    return {"proceed": True, "error": str(e)}
```

### 3. Logging

- Use structured logging
- Include timestamps and session IDs
- Don't log sensitive information
- Rotate logs regularly

### 4. Security

- Validate all inputs
- Sanitize file paths
- Check permissions
- Implement rate limiting

## Advanced Patterns

### 1. Chaining Hooks

Configure multiple hooks for the same event:

```json
{
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {"type": "command", "command": "python security_check.py"},
        {"type": "command", "command": "python audit_log.py"}
      ]
    }
  ]
}
```

### 2. Conditional Processing

```python
def process_hook(data):
    # Different logic based on context
    if is_production_environment():
        return validate_production_command(data)
    else:
        return {"proceed": True}
```

### 3. Integration with External Systems

```python
async def process_hook(data):
    # Send to external monitoring
    await send_to_monitoring_service(data)
    
    # Check with policy server
    policy_result = await check_policy(data)
    
    return {"proceed": policy_result.allowed}
```

## Debugging Hooks

### 1. Enable Debug Mode

```bash
export KHIVE_DEBUG=true
```

### 2. Test Hooks Manually

```bash
echo '{"tool_name": "Bash", "tool_input": {"command": "ls"}}' | python my_hook.py
```

### 3. Check Hook Logs

```bash
# View hook execution logs
tail -f ~/.khive_claude/hooks.log
```

### 4. Common Issues

| Issue | Solution |
|-------|----------|
| Hook not triggering | Check `.claude/settings.json` format |
| Hook blocking all operations | Ensure `proceed: true` is returned |
| Performance issues | Profile hook execution time |
| Missing data | Verify hook input structure |

## Examples

### Security Hook

```python
# Block dangerous file operations
def handle_pre_edit(data):
    file_paths = data.get("tool_input", {}).get("file_paths", [])
    
    for path in file_paths:
        if path.startswith("/etc/") or path.startswith("/sys/"):
            return {
                "proceed": False,
                "reason": f"Access to system file {path} is restricted"
            }
    
    return {"proceed": True}
```

### Audit Hook

```python
# Log all command executions
async def handle_post_command(data):
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": os.environ.get("USER"),
        "session": data.get("session_id"),
        "command": data.get("tool_input", {}).get("command"),
        "exit_code": data.get("tool_output", {}).get("exit_code"),
        "duration": data.get("tool_output", {}).get("duration_ms")
    }
    
    await save_to_audit_log(audit_entry)
    return {"proceed": True}
```

### Notification Hook

```python
# Send alerts for errors
def handle_notification(data):
    if data.get("severity") == "error":
        send_alert({
            "message": data.get("message"),
            "timestamp": data.get("timestamp"),
            "session": data.get("session_id")
        })
    
    return {"proceed": True}
```

## Next Steps

1. Review the [khive_claude implementation](../src/khive_claude/hooks/) for real examples
2. Start with simple logging hooks
3. Gradually add more complex logic
4. Monitor performance impact
5. Share your hooks with the community!