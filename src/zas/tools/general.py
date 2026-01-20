# tools_general.py - tools voor algemeen


from src.zas.core.helpers import mcp


# =====================================================
# TOOLS: ALGEMEEN — gebruikt door: General-Agent
# =====================================================

@mcp.tool
def ping() -> str:
	"""Controleer of MCP actief is."""
	return "pong"