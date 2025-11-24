# tools_reporting.py - tools voor reporting & export


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
# TOOLS: REPORTING & EXPORT — gebruikt door: Reporting-Agent
# =====================================================

@mcp.tool
def tickets_export_csv(query: str, path: str = "tickets_export.csv", limit: int = 1000):
    """[KB-Agent]

Exporteer gevonden tickets naar CSV (id, subject, status, priority, assignee_id, requester_id, organization_id, tags, created_at, updated_at).
    """
    try:
        rows = _paginate_search(query=query, limit=limit)
        fields = ["id","subject","status","priority","assignee_id","requester_id","organization_id","tags","created_at","updated_at"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for t in rows:
                w.writerow({k: t.get(k) for k in fields})
        return {"ok": True, "path": os.path.abspath(path), "count": len(rows)}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}

# ---------- SERVER START ----------
if __name__ == "__main__":
    # Start de MCP HTTP-server op /mcp
    # Let op: Agent-URL MOET eindigen op /mcp
    mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp")
