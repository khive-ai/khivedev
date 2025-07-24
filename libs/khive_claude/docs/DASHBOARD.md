# khive_claude Dashboard

Real-time monitoring dashboard for Claude Code hook events.

## Features

- **📊 Real-time Metrics**: Track total events, activity rate, sessions, and most active hooks
- **📈 Interactive Charts**: Visualize hook distribution and activity timeline with multiple time ranges
- **🔍 Advanced Filtering**: Filter by event type, tool, session, and search across all event data
- **⏰ Activity Timeline**: View activity patterns for Today, Last 7 Days, Last 30 Days, This Month, or All Time
- **📥 Data Export**: Export event data as CSV for external analysis
- **🔄 Auto-refresh**: Configurable auto-refresh intervals
- **🔴 WebSocket Support**: Real-time event streaming (optional)

## Usage

Start the dashboard:
```bash
cd khive_claude
uv run python -m khive_claude.cli dashboard --port 8502
```

## Configuration

The dashboard can be configured using environment variables:

- `KHIVE_REFRESH_RATE`: Default auto-refresh rate in seconds (default: 5)
- `KHIVE_MAX_EVENTS`: Maximum events to display (default: 500)
- `KHIVE_DEFAULT_TIME_RANGE`: Default timeline range (default: "Today")
- `KHIVE_ENABLE_WEBSOCKET`: Enable WebSocket support (default: true)
- `KHIVE_WEBSOCKET_PORT`: WebSocket server port (default: 8766)

Example:
```bash
export KHIVE_REFRESH_RATE=10
export KHIVE_DEFAULT_TIME_RANGE="Last 7 Days"
uv run python -m khive_claude.cli dashboard
```

## Hook Types

The dashboard monitors these Claude Code hook events:

- **Pre/Post Command**: Bash command execution
- **Pre/Post Edit**: File modifications
- **Pre/Post Agent Spawn**: Task agent operations
- **Prompt Submitted**: User prompt submissions
- **Notification**: System notifications

## Tips

- Click on the donut chart segments to see details
- Use the time range selector to analyze patterns over different periods
- Export data for deeper analysis in external tools
- Use filters to focus on specific event types or sessions
- The red "Now" line on Today's timeline shows current time

## Requirements

- Python 3.8+
- Streamlit
- Plotly
- pandas
- SQLite database (created automatically)