# tools_general.py - tools voor algemeen


from core import (
    mcp,
    _get,
    _post,
    _put,
    _paginate_search,
    _jira_get,
    _conf_get,
    os,
    csv,
    time,
    math,
    traceback,
    requests,
    pd,
)

# =====================================================
# TOOLS: ALGEMEEN — gebruikt door: General-Agent
# =====================================================

@mcp.tool
def ping() -> str:
    """Controleer of MCP actief is."""
    return "pong"


# ---------- ZOEKEN (verbeterde variant) ----------
