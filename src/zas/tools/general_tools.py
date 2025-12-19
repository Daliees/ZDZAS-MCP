"""General utility MCP tools."""

from typing import Any, Dict


class GeneralTools:
    """MCP tools for general utilities."""
    
    @staticmethod
    def ping() -> str:
        """
        [General-Agent] Check if MCP is active.
        
        Returns:
            Simple pong response
        """
        return "pong"
