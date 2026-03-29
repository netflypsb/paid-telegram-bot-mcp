"""Paid Telegram Bot MCP Server — Enterprise Telegram bot management for any AI agent."""

__version__ = "0.1.0"


def main():
    """Entry point for the paid-telegram-bot command."""
    from .server import run_server
    run_server()
