# tools_jira.py - tools voor Jira

from core import mcp, _jira_get
import os
import traceback
import requests

# ---- JIRA ENV ----
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

@mcp.tool
def jira_get_issue(issue_key: str, max_comments: int = 5):
    """
    [Jira-Agent]

    Haal details op van een Jira-issue (bijv. 'TGR-123') inclusief laatste comments.
    """
    try:
        if not issue_key:
            return {"ok": False, "error": "issue_key mag niet leeg zijn."}

        data = _jira_get(f"/rest/api/3/issue/{issue_key}")
        fields = data.get("fields", {}) or {}
        status = (fields.get("status") or {}).get("name")
        assignee = fields.get("assignee") or {}
        assignee_name = assignee.get("displayName")
        summary = fields.get("summary")

        # Comments ophalen (kan via 'fields.comment.comments' of via aparte endpoint)
        comments_block = fields.get("comment") or {}
        comments = comments_block.get("comments") or []

        # Sorteer op created en pak de laatste N
        comments_sorted = sorted(
            comments,
            key=lambda c: c.get("created", ""),
        )
        latest = comments_sorted[-max_comments:] if comments_sorted else []

        # Minimaliseer comment-inhoud
        simplified_comments = []
        for c in latest:
            author = (c.get("author") or {}).get("displayName")
            body = c.get("body")
            # body kan bij Cloud een rich object zijn; we pakken een simpele fallback
            if isinstance(body, dict) and "content" in body:
                # heel ruwe extract
                text = []
                for b1 in body.get("content", []):
                    for b2 in b1.get("content", []):
                        t = b2.get("text")
                        if t:
                            text.append(t)
                body_text = "\n".join(text)
            else:
                body_text = str(body) if body is not None else ""

            simplified_comments.append(
                {
                    "author": author,
                    "created": c.get("created"),
                    "updated": c.get("updated"),
                    "body": body_text[:2000],  # truncate voor de agent
                }
            )

        return {
            "ok": True,
            "key": data.get("key"),
            "summary": summary,
            "status": status,
            "assignee": assignee_name,
            "updated": fields.get("updated"),
            "latest_comments": simplified_comments,
            "raw": {"id": data.get("id"), "self": data.get("self")},
        }

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        return {
            "ok": False,
            "error": f"HTTPError bij Jira issue {issue_key} (status {status})",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()}