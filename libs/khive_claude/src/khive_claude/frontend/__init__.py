# Copyright (c) 2025, HaiyangLi <quantocean.li at gmail dot com>
#
# SPDX-License-Identifier: MIT

"""
Frontend components for Claude Code Observability.

Provides Streamlit dashboard and real-time WebSocket server for monitoring
Claude Code hook events and system interactions.
"""

from .realtime_server import HookEventWebSocketServer
from .streamlit_dashboard import ClaudeCodeObservabilityDashboard

__all__ = [
    "ClaudeCodeObservabilityDashboard",
    "HookEventWebSocketServer",
]
