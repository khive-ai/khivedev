# API Reference

## Database Models

### HookEvent

The core model for storing hook events.

```python
from khive_claude.hooks.hook_event import HookEvent, HookEventContent

# Create an event
event = HookEvent(
    content=HookEventContent(
        event_type="pre_command",
        tool_name="Bash",
        command="ls -la",
        session_id="abc123",
        metadata={"cwd": "/home/user"}
    )
)

# Save to database
await event.save()

# Query events
recent_events = await HookEvent.get_recent(limit=100)
events_by_type = await HookEvent.get_by_type("pre_command")
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier (UUID) |
| `created_datetime` | `datetime` | Event timestamp |
| `content` | `HookEventContent` | Event details |

### HookEventContent

Structured content for hook events.

```python
class HookEventContent:
    event_type: str          # Hook type (pre_command, post_edit, etc.)
    tool_name: str          # Tool used (Bash, Edit, Write, etc.)
    command: Optional[str]   # Command executed (for Bash)
    output: Optional[str]    # Command output
    file_paths: List[str]    # Files affected
    session_id: Optional[str] # Session identifier
    metadata: Dict[str, Any] # Additional data
```

## Database Adapter

### Usage

```python
from khive_claude.adapters.sqlite_adapter import DatabaseAdapter

# Initialize adapter (auto-creates database)
adapter = DatabaseAdapter()

# Save event
await adapter.save_event(event)

# Query events
events = await adapter.get_recent_events(limit=50)
events_by_type = await adapter.get_events_by_type("pre_edit")
```

### Methods

#### `save_event(event: HookEvent) -> None`

Save a hook event to the database.

#### `get_recent_events(limit: int = 100) -> List[HookEvent]`

Retrieve the most recent events.

#### `get_events_by_type(event_type: str, limit: int = 100) -> List[HookEvent]`

Get events of a specific type.

#### `get_events_by_session(session_id: str) -> List[HookEvent]`

Get all events for a session.

#### `get_events_in_range(start: datetime, end: datetime) -> List[HookEvent]`

Get events within a time range.

## CLI Interface

### Commands

```bash
# Start dashboard
khive-claude dashboard [--port PORT] [--host HOST]

# Check system status
khive-claude status

# Start WebSocket server
khive-claude server [--port PORT]

# Export data
khive-claude export [--format csv|json] [--output FILE]
```

### Python API

```python
from khive_claude.cli import cli

# Run CLI programmatically
cli(['dashboard', '--port', '8502'])
```

## WebSocket API

### Server

```python
from khive_claude.hooks.hook_event import HookEventBroadcaster

# Start WebSocket server
await HookEventBroadcaster.start_server(port=8766)

# Broadcast event
await HookEventBroadcaster.broadcast(event)
```

### Client

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8766');

// Listen for events
ws.onmessage = (event) => {
    const hookEvent = JSON.parse(event.data);
    console.log('New event:', hookEvent);
};

// Send ping
ws.send(JSON.stringify({type: 'ping'}));
```

### Message Format

```json
{
    "type": "event",
    "data": {
        "id": "uuid",
        "created_datetime": "2024-01-01T00:00:00Z",
        "event_type": "pre_command",
        "tool_name": "Bash",
        "command": "ls -la",
        "session_id": "abc123"
    }
}
```

## Hook Script Helpers

### shield Function

Protect async operations from cancellation:

```python
from khive_claude.hooks.hook_event import shield

# Ensure database write completes
await shield(event.save())
```

### Event Broadcasting

```python
from khive_claude.hooks.hook_event import HookEventBroadcaster

# Broadcast to all connected clients
await HookEventBroadcaster.broadcast(event)

# Get subscriber count
count = HookEventBroadcaster.get_subscriber_count()
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KHIVE_DB_PATH` | `~/.khive_claude/events.db` | Database location |
| `KHIVE_DEBUG` | `false` | Enable debug logging |
| `KHIVE_REFRESH_RATE` | `5` | Dashboard refresh interval |
| `KHIVE_MAX_EVENTS` | `500` | Max events to display |
| `KHIVE_DEFAULT_TIME_RANGE` | `Today` | Default timeline view |
| `KHIVE_ENABLE_WEBSOCKET` | `true` | Enable WebSocket server |
| `KHIVE_WEBSOCKET_PORT` | `8766` | WebSocket port |

## Error Handling

### Database Errors

```python
try:
    await event.save()
except DatabaseError as e:
    logger.error(f"Failed to save event: {e}")
    # Event is lost but hook continues
```

### Hook Errors

```python
def safe_hook_handler(func):
    def wrapper(data):
        try:
            return func(data)
        except Exception as e:
            # Log but don't block Claude
            logger.error(f"Hook error: {e}")
            return {"proceed": True, "error": str(e)}
    return wrapper
```

## Performance Considerations

### Database

- SQLite with WAL mode for concurrent access
- Indexes on `created_datetime`, `event_type`, and `session_id`
- Automatic cleanup of events older than 30 days

### Memory

- Events cached for 2 seconds in dashboard
- Maximum 500 events loaded at once
- WebSocket broadcasts are fire-and-forget

### CPU

- Hook scripts should complete in <100ms
- Async I/O for all database operations
- Background tasks for cleanup

## Migration Guide

### From v0.x to v1.0

```python
# Old format
event = {
    "type": "command",
    "data": {...}
}

# New format
event = HookEvent(
    content=HookEventContent(
        event_type="pre_command",
        tool_name="Bash",
        ...
    )
)
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development setup and guidelines.