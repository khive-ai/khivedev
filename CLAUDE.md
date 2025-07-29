# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**khivedev** is Ocean's intelligent tooling and interface system for Claude Code observability and monitoring. The project consists of two main components:

1. **khive_claude** - A Python library that provides real-time monitoring and observability for Claude Code hook events
2. **claude_proxy** - A FastAPI proxy server that enables using Claude Code from other environments like Jupyter notebooks

The system captures all Claude Code tool interactions (Bash commands, file edits, Task spawns) via hooks, stores them in SQLite, and provides real-time visualization through a Streamlit dashboard.

## Development Commands

### Setup and Installation
```bash
# Install dependencies (uses uv workspace)
uv sync

# Install khive_claude library in development mode
cd libs/khive_claude
uv pip install -e .
```

### Running the System
```bash
# Start the complete monitoring system (dashboard + WebSocket server)
uv run python -m khive_claude.cli start

# Start only the dashboard on port 8501
uv run python -m khive_claude.cli dashboard --port 8501

# Start only the WebSocket server on port 8765
uv run python -m khive_claude.cli server --port 8765

# Check system status
uv run python -m khive_claude.cli status
```

### Testing
```bash
# Run the hook integration test
cd libs/khive_claude
uv run python test_claude_integration.py
```

### Code Quality
```bash
# Format code
uv run black --line-length 88 .
uv run isort .

# Lint code
uv run ruff check .
uv run ruff format .
```

## Architecture Overview

### Core Components

**Hook System** (`libs/khive_claude/src/khive_claude/hooks/`)
- Lightweight Python scripts that capture Claude Code events
- Each hook corresponds to a specific Claude Code event type:
  - `prompt_submitted.py` - User submits a prompt
  - `pre_command.py`/`post_command.py` - Bash command execution
  - `pre_edit.py`/`post_edit.py` - File modifications
  - `pre_agent_spawn.py`/`post_agent_spawn.py` - Task agent operations
  - `notification.py` - System notifications

**Event Storage** (`libs/khive_claude/src/khive_claude/hooks/hook_event.py`)
- Uses LionAGI's Node system with Pydantic models
- Async SQLite storage via LionAGI adapters
- Real-time event broadcasting system with subscriber pattern

**Dashboard** (`libs/khive_claude/src/khive_claude/frontend/streamlit_dashboard.py`)
- Streamlit-based real-time monitoring interface
- Displays system metrics, hook distribution, activity timeline
- WebSocket integration for live updates
- Event filtering and search capabilities

**CLI Interface** (`libs/khive_claude/src/khive_claude/cli.py`)
- Click-based command-line interface
- Manages dashboard and WebSocket server processes
- Provides system status and configuration

### Data Flow
```
Claude Code → Hook Scripts → SQLite Database → Streamlit Dashboard
                ↓
            WebSocket Server → Real-time Updates
```

## Configuration

### Claude Code Hooks Setup
The system requires specific hook configuration in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [{"type": "command", "command": "uv run python -m khive_claude.hooks.pre_edit"}]
      },
      {
        "matcher": "Bash", 
        "hooks": [{"type": "command", "command": "uv run python -m khive_claude.hooks.pre_command"}]
      },
      {
        "matcher": "Task",
        "hooks": [{"type": "command", "command": "uv run python -m khive_claude.hooks.pre_agent_spawn"}]
      }
    ],
    "PostToolUse": [
      // Similar structure for post hooks
    ],
    "UserPromptSubmit": [
      {"hooks": [{"type": "command", "command": "uv run python -m khive_claude.hooks.prompt_submitted"}]}
    ]
  }
}
```

### Environment Variables
```bash
export KHIVE_REFRESH_RATE=5          # Dashboard refresh interval
export KHIVE_MAX_EVENTS=500          # Max events to display
export KHIVE_DEFAULT_TIME_RANGE=Today # Default timeline view
export KHIVE_ENABLE_WEBSOCKET=true   # Enable WebSocket support
export KHIVE_DEBUG=true              # Enable debug logging
```

## Key Dependencies

- **LionAGI** (`lionagi[postgres, sqlite]>=0.14.8`) - Core framework providing Node system, async adapters, and concurrency utilities
- **Streamlit** (`>=1.47.0`) - Dashboard framework
- **WebSockets** (`>=15.0.1`) - Real-time communication
- **Plotly** (`>=6.2.0`) - Charts and visualizations
- **Click** - CLI framework
- **FastAPI** - Proxy server (claude_proxy component)

## Directory Structure

```
khivedev/
├── libs/khive_claude/           # Main monitoring library
│   ├── src/khive_claude/
│   │   ├── hooks/              # Hook event handlers
│   │   ├── frontend/           # Dashboard and WebSocket server
│   │   └── cli.py             # Command-line interface
│   ├── docs/                   # Documentation
│   └── test_claude_integration.py
├── infra/claude_proxy/         # FastAPI proxy for external access
├── live-stream/               # Development notebooks
└── .claude/settings.json     # Hook configuration
```

## Development Workflow

1. **Hook Development**: Create new hooks by following the pattern in existing hook files
2. **Event Schema**: Use `HookEventContent` TypedDict for consistent event structure
3. **Database**: Events automatically stored via LionAGI's async adapters
4. **Real-time Updates**: Use `HookEventBroadcaster` for live dashboard updates
5. **Testing**: Run `test_claude_integration.py` to verify hook functionality

## Integration Points

- **LionAGI Integration**: Uses LionAGI's Node system, async adapters, and concurrency utilities
- **Claude Code Hooks**: Integrates with Claude Code's native hook system
- **WebSocket Communication**: Real-time event streaming to dashboard
- **External Access**: Proxy server enables Claude Code usage from Jupyter/other environments