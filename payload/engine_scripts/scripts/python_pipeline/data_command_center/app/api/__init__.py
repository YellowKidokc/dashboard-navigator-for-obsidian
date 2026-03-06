"""API module for HTTP endpoints."""
from .obsidian_bridge import app, run_bridge

__all__ = ['app', 'run_bridge']
