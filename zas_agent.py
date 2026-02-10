from __future__ import annotations

from typing import List, Dict, Any, Optional

import os
import json
import math
import time
import csv
import traceback

from pydantic import BaseModel

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain.agents import create_agent

from core import (
    _get, _put, _post, _paginate_search,
    _jira_get, _conf_get,
    CONF_BASE_URL,
)


# ---------------------------------------------------------------------------
# LangChain tool definitions — direct calls to core.py API helpers
# ---------------------------------------------------------------------------

# ===== Tickets =====

@tool
def tickets_search(query: str, limit: int = 50) -> dict:
    """Zoek Zendesk tickets met Zendesk zoeksyntaxis.
    Voorbeeld: 'type:ticket status<solved created>2025-01-01'
    Returns: count + subset velden."""
    try:
        raw = _paginate_search(query=query, limit=limit)
        items = []
        for hit in raw:
            items.append(
                {
                    "id": hit.get("id"),
                    "subject": hit.get("subject"),
                    "status": hit.get("status"),
                    "priority": hit.get("priority"),
                    "assignee_id": hit.get("assignee_id"),
                    "requester_id": hit.get("requester_id"),
                    "organization_id": hit.get("organization_id"),
                    "tags": hit.get("tags", []),
                    "created_at": hit.get("created_at"),
                    "updated_at": hit.get("updated_at"),
                }
            )
        return {"count": len(items), "tickets": items}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}


@tool
def ticket_get(ticket_id: int) -> dict:
    """Haal volledige ticketdetails op."""
    try:
        data = _get(f"/tickets/{ticket_id}.json")
        return {"ok": True, "ticket": data.get("ticket")}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}


@tool
def ticket_comments(ticket_id: int, include_public: bool = True) -> dict:
    """Haal alle comments (publiek + intern) op. Filter op public wanneer gewenst."""
    try:
        data = _get(f"/tickets/{ticket_id}/comments.json")
        comments = data.get("comments", [])
        if include_public:
            comments = [c for c in comments if c.get("public", False)]
        return {"ok": True, "count": len(comments), "comments": comments}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}


@tool
def ticket_add_internal_note(ticket_id: int, body: str) -> dict:
    """Voeg een *interne opmerking* (private comment) toe aan een Zendesk-ticket.
    De opmerking is NIET zichtbaar voor de requester, alleen voor agents."""
    try:
        text = (body or "").strip()
        if not text:
            return {
                "ok": False,
                "error": "De body van de interne opmerking mag niet leeg zijn.",
            }

        payload = {
            "ticket": {
                "comment": {
                    "body": text,
                    "public": False,
                }
            }
        }

        api_response = _put(f"/tickets/{ticket_id}.json", payload)

        latest_body = None
        try:
            comments_data = _get(f"/tickets/{ticket_id}/comments.json")
            comments = comments_data.get("comments", [])
            if comments:
                latest_body = comments[-1].get("body")
        except Exception:
            pass

        return {
            "ok": True,
            "ticket_id": ticket_id,
            "internal_note_preview": latest_body,
            "raw_api_response": api_response,
        }

    except Exception as e:
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()}


@tool
def ticket_categorize(query: str, limit: int = 300) -> dict:
    """Ken een categorie toe aan elk ticket (heuristisch).
    Handig voor routing en volumestatistiek per categorie."""
    try:
        tickets = _paginate_search(query=query, limit=limit)
        categories = {
            "login": ["login", "password", "2fa", "two factor", "authentication", "auth code", "verify code"],
            "billing": ["invoice", "payment", "refund", "charged", "billing", "credit card"],
            "bug": ["error", "crash", "not working", "broken", "fails", "issue", "bug"],
            "feature": ["feature request", "can you add", "improvement", "roadmap"],
            "account": ["deactivate account", "delete account", "account access", "subscription", "upgrade plan"],
        }

        def pick_category(subject: str) -> str:
            s = (subject or "").lower()
            for cat, keywords in categories.items():
                if any(kw in s for kw in keywords):
                    return cat
            return "other"

        labeled = []
        dist = {}
        for t in tickets:
            cat = pick_category(t.get("subject", ""))
            labeled.append({"id": t.get("id"), "subject": t.get("subject"), "category": cat})
            dist[cat] = dist.get(cat, 0) + 1
        return {"ok": True, "distribution": dist, "labeled": labeled[:25], "total_tickets": len(tickets)}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}


@tool
def ticket_generate_draft(query: str, limit: int = 20) -> dict:
    """Bundel opgeloste tickets over hetzelfde probleem zodat de agent daar een KB-artikel uit kan schrijven."""
    try:
        solved_query = query if "status:" in query else f"{query} status:solved"
        tickets = _paginate_search(query=solved_query, limit=limit)
        bundle = []
        for t in tickets:
            tid = t.get("id")
            subject = t.get("subject") or ""
            try:
                raw_comments = _get(f"/tickets/{tid}/comments.json").get("comments", [])
                public_comments = [c.get("body", "") for c in raw_comments if c.get("public", False)]
            except Exception:
                public_comments = []
            summarized = ""
            if public_comments:
                first = public_comments[0].strip().replace("\r", " ").replace("\n", " ")
                summarized = (first[:220] + "...") if len(first) > 220 else first
            bundle.append({"id": tid, "subject": subject, "problem_summary": summarized})
            time.sleep(0.1)
        lines = [f"- Ticket {b['id']} :: '{b['subject']}' :: Mogelijk probleem: {b['problem_summary']}" for b in bundle]
        combined_text = (
            "Deze tickets lijken over hetzelfde of vergelijkbare probleem te gaan.\n"
            "Gebruik dit om een KB-artikel te schrijven met secties: "
            "PROBLEEM / OORZAAK / OPLOSSING (STAPPEN) / WANNEER ESCALEREN.\n\n"
            + "\n".join(lines)
        )
        return {
            "ok": True,
            "tickets_used": len(bundle),
            "draft_context": combined_text[:10000],
            "hint": "Gebruik dit om een kennisbankartikel te schrijven.",
        }
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}


@tool
def ticket_solution_rate(query: str, limit: int = 200) -> dict:
    """Meet hoe vaak tickets direct opgelost worden zonder reopen."""
    try:
        tickets = _paginate_search(query=query, limit=limit)
        total = len(tickets)
        direct = 0
        reopened_any = 0
        for t in tickets:
            tid = t.get("id")
            if not tid:
                continue
            try:
                metrics_raw = _get(f"/tickets/{tid}/metrics.json")
                metrics = metrics_raw.get("ticket_metric", {})
            except Exception:
                metrics = {}
            reopens = metrics.get("reopens", 0) or 0
            replies = metrics.get("replies", 0) or 0
            status = t.get("status")
            if reopens > 0:
                reopened_any += 1
            if status == "solved" and reopens == 0 and replies <= 1:
                direct += 1
            time.sleep(0.1)
        rate = (direct / total * 100.0) if total > 0 else 0.0
        return {
            "ok": True,
            "total": total,
            "directly_solved": direct,
            "reopened": reopened_any,
            "direct_resolution_rate_pct": round(rate, 1),
        }
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}


@tool
def ticket_metrics(ticket_id: int) -> dict:
    """Haal ticket metrics op (o.a. first/full resolution, requester/agent wait times)."""
    try:
        data = _get(f"/tickets/{ticket_id}/metrics.json")
        return {"ok": True, "metrics": data.get("ticket_metric")}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}


@tool
def tickets_tag_stats(query: str, limit: int = 200) -> dict:
    """Aggegreer top-tags, statussen en assignees over gevonden tickets."""
    try:
        raw = _paginate_search(query=query, limit=limit)
        tag_counts = {}
        status_counts = {}
        assignee_counts = {}
        for t in raw:
            for tag in t.get("tags", []) or []:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            st = t.get("status", "unknown")
            status_counts[st] = status_counts.get(st, 0) + 1
            asg = str(t.get("assignee_id") or "unassigned")
            assignee_counts[asg] = assignee_counts.get(asg, 0) + 1

        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:25]
        top_assignees = sorted(assignee_counts.items(), key=lambda x: x[1], reverse=True)[:25]
        status_sorted = sorted(status_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            "ok": True,
            "total_tickets": len(raw),
            "status_distribution": status_sorted,
            "top_tags": top_tags,
            "top_assignees_by_ticket_count": top_assignees,
        }
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}


@tool
def tickets_analyze(
    query: str,
    limit: int = 200,
    enrich_with_metrics: bool = True,
    metrics_sample: int = 50,
) -> dict:
    """End-to-end analyse: zoekt tickets, berekent verdelingen, en (optioneel)
    haalt metrics op voor een steekproef om doorlooptijden/SLA te schatten."""
    try:
        tickets = _paginate_search(query=query, limit=limit)
        if not tickets:
            return {"ok": True, "summary": {"total": 0}, "insights": {}}

        def _inc(d, k):
            d[k] = d.get(k, 0) + 1

        by_status, by_priority, by_assignee, tag_counts = {}, {}, {}, {}
        for t in tickets:
            _inc(by_status, t.get("status") or "unknown")
            _inc(by_priority, t.get("priority") or "none")
            _inc(by_assignee, str(t.get("assignee_id") or "unassigned"))
            for tag in t.get("tags", []) or []:
                _inc(tag_counts, tag)

        metrics_rows = []
        if enrich_with_metrics:
            sample_ids = [t["id"] for t in tickets[:max(0, min(metrics_sample, len(tickets)))]]
            for tid in sample_ids:
                try:
                    m = _get(f"/tickets/{tid}/metrics.json").get("ticket_metric", {})
                except Exception:
                    m = {}

                def _mins(x):
                    if isinstance(x, dict):
                        return {k: v for k, v in x.items() if k in ("calendar", "business")}
                    return x

                metrics_rows.append({
                    "ticket_id": tid,
                    "first_resolution": _mins(m.get("first_resolution_time_in_minutes")),
                    "full_resolution": _mins(m.get("full_resolution_time_in_minutes")),
                    "requester_wait": _mins(m.get("requester_wait_time_in_minutes")),
                    "agent_wait": _mins(m.get("agent_wait_time_in_minutes")),
                    "on_hold": _mins(m.get("on_hold_time_in_minutes")),
                    "reopens": m.get("reopens"),
                    "replies": m.get("replies"),
                })
                time.sleep(0.1)

        def _extract_minutes(arr, key, sub="calendar"):
            vals = []
            for r in arr:
                v = r.get(key)
                if isinstance(v, dict):
                    mv = v.get(sub)
                    if isinstance(mv, (int, float)):
                        vals.append(mv)
                elif isinstance(v, (int, float)):
                    vals.append(v)
            return vals

        insights = {
            "status_distribution": sorted(by_status.items(), key=lambda x: x[1], reverse=True),
            "priority_distribution": sorted(by_priority.items(), key=lambda x: x[1], reverse=True),
            "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:25],
            "top_assignees_by_ticket_count": sorted(by_assignee.items(), key=lambda x: x[1], reverse=True)[:25],
        }

        if metrics_rows:
            cal_full = _extract_minutes(metrics_rows, "full_resolution", "calendar")
            biz_full = _extract_minutes(metrics_rows, "full_resolution", "business")
            cal_first = _extract_minutes(metrics_rows, "first_resolution", "calendar")
            reopen_counts = [r.get("reopens") for r in metrics_rows if isinstance(r.get("reopens"), (int, float))]
            reply_counts = [r.get("replies") for r in metrics_rows if isinstance(r.get("replies"), (int, float))]

            def _summary(vs):
                if not vs:
                    return {}
                vs_sorted = sorted(vs)
                n = len(vs_sorted)
                p50 = vs_sorted[n // 2] if n % 2 else (vs_sorted[n // 2 - 1] + vs_sorted[n // 2]) / 2
                p90 = vs_sorted[math.floor(0.9 * (n - 1))]
                return {"n": n, "mean": sum(vs_sorted) / n, "p50": p50, "p90": p90}

            insights["metrics_summary_minutes"] = {
                "first_resolution_calendar": _summary(cal_first),
                "full_resolution_calendar": _summary(cal_full),
                "full_resolution_business": _summary(biz_full),
                "reopens": _summary(reopen_counts),
                "replies": _summary(reply_counts),
            }

        return {
            "ok": True,
            "summary": {"total": len(tickets), "metrics_sampled": len(metrics_rows)},
            "insights": insights,
            "sample_metrics": metrics_rows[:5],
        }

    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}


# ===== Kennisbank =====

@tool
def kb_generate_draft(query: str, limit: int = 20) -> dict:
    """Genereer concept kennisbank-artikel op basis van opgeloste tickets."""
    try:
        tickets = _paginate_search(query + " status:solved", limit=limit)
        bundle = []
        for t in tickets:
            tid = t["id"]
            comments = []
            try:
                cdata = _get(f"/tickets/{tid}/comments.json").get("comments", [])
                comments = [c["body"] for c in cdata if c.get("public", False)]
            except Exception:
                pass
            bundle.append({
                "id": tid,
                "subject": t.get("subject"),
                "summary": (comments[0][:200] if comments else ""),
                "comments": comments,
            })

        combined_text = "\n\n".join(
            [f"### Ticket {b['id']}: {b['subject']}\n{b['summary']}" for b in bundle]
        )

        return {
            "ok": True,
            "tickets_used": len(bundle),
            "draft_context": combined_text[:10000],
            "hint": "Gebruik deze context in de agent om een kennisbankartikel te schrijven.",
        }
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}


@tool
def kb_search_articles(
    query: str,
    limit: int = 20,
    label_names: str = "",
    locale: str = "",
) -> dict:
    """Zoek in Zendesk Help Center-artikelen (kennisbank)."""
    try:
        q = (query or "").strip()
        if not q and not label_names:
            return {"ok": False, "error": "Geef minimaal een query of label_names op."}

        per_page = min(100, max(1, limit))
        params = {"per_page": per_page}
        if q:
            params["query"] = q
        if label_names:
            params["label_names"] = label_names

        data = _get("/help_center/articles/search.json", params)
        raw_results = data.get("results", [])

        if locale:
            raw_results = [a for a in raw_results if a.get("locale") == locale]

        raw_results = raw_results[:limit]

        articles = []
        for art in raw_results:
            articles.append(
                {
                    "id": art.get("id"),
                    "title": art.get("title"),
                    "snippet": art.get("snippet"),
                    "html_url": art.get("html_url") or art.get("url"),
                    "locale": art.get("locale"),
                    "draft": art.get("draft"),
                    "label_names": art.get("label_names"),
                    "section_id": art.get("section_id"),
                    "created_at": art.get("created_at"),
                    "updated_at": art.get("updated_at"),
                }
            )

        return {"ok": True, "count": len(articles), "articles": articles}

    except Exception as e:
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()}


@tool
def kb_create_draft_article(
    title: str,
    body: str,
    section_id: Optional[int] = None,
    locale: str = "nl",
    permission_group_id: Optional[int] = None,
    user_segment_id: Optional[int] = None,
) -> dict:
    """Maak een concept-kennisbankartikel aan in Zendesk Help Center."""
    try:
        t = (title or "").strip()
        b = (body or "").strip()
        if not t:
            return {"ok": False, "error": "Title mag niet leeg zijn."}
        if not b:
            return {"ok": False, "error": "Body mag niet leeg zijn."}

        pg = permission_group_id or os.getenv("ZENDESK_KB_PERMISSION_GROUP_ID")
        us = user_segment_id or os.getenv("ZENDESK_KB_USER_SEGMENT_ID")
        if not pg or not us:
            return {
                "ok": False,
                "error": (
                    "permission_group_id en user_segment_id ontbreken. "
                    "Geef ze als argument of zet ZENDESK_KB_PERMISSION_GROUP_ID en "
                    "ZENDESK_KB_USER_SEGMENT_ID in .env."
                ),
            }

        sid_source = section_id if section_id not in (None, 0) else os.getenv("ZENDESK_KB_CONCEPT_SECTION_ID")
        if not sid_source:
            return {
                "ok": False,
                "error": (
                    "Geen geldige section_id opgegeven en ZENDESK_KB_CONCEPT_SECTION_ID ontbreekt."
                ),
            }

        try:
            sid = int(str(sid_source))
            pg = int(str(pg))
            us = int(str(us))
        except Exception:
            return {
                "ok": False,
                "error": "section_id, permission_group_id en user_segment_id moeten integers zijn.",
            }

        payload = {
            "article": {
                "title": t,
                "body": b,
                "locale": locale,
                "permission_group_id": pg,
                "user_segment_id": us,
                "draft": True,
            },
            "notify_subscribers": False,
        }

        data = _post(f"/help_center/{locale}/sections/{sid}/articles.json", payload)
        article = data.get("article") or data

        return {
            "ok": True,
            "article_id": article.get("id"),
            "html_url": article.get("html_url"),
            "locale": article.get("locale"),
            "draft": article.get("draft"),
            "section_id": article.get("section_id"),
            "raw": article,
        }

    except Exception as e:
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()}


# ===== Reporting =====

@tool
def tickets_export_csv(
    query: str,
    path: str = "tickets_export.csv",
    limit: int = 1000,
) -> dict:
    """Exporteer gevonden tickets naar CSV."""
    try:
        rows = _paginate_search(query=query, limit=limit)
        fields = [
            "id", "subject", "status", "priority", "assignee_id",
            "requester_id", "organization_id", "tags", "created_at", "updated_at",
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for t in rows:
                w.writerow({k: t.get(k) for k in fields})
        return {"ok": True, "path": os.path.abspath(path), "count": len(rows)}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}


# ===== General =====

@tool
def ping() -> str:
    """Controleer of de agent actief is."""
    return "pong"


# ===== Jira =====

@tool
def jira_get_issue(issue_key: str, max_comments: int = 5) -> dict:
    """Haal details op van een Jira-issue (bijv. 'TGR-123') inclusief laatste comments."""
    try:
        if not issue_key:
            return {"ok": False, "error": "issue_key mag niet leeg zijn."}

        data = _jira_get(f"/rest/api/3/issue/{issue_key}")
        fields = data.get("fields", {}) or {}
        status = (fields.get("status") or {}).get("name")
        assignee = fields.get("assignee") or {}
        assignee_name = assignee.get("displayName")
        summary = fields.get("summary")

        comments_block = fields.get("comment") or {}
        comments = comments_block.get("comments") or []

        comments_sorted = sorted(comments, key=lambda c: c.get("created", ""))
        latest = comments_sorted[-max_comments:] if comments_sorted else []

        simplified_comments = []
        for c in latest:
            author = (c.get("author") or {}).get("displayName")
            body = c.get("body")
            if isinstance(body, dict) and "content" in body:
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
                    "body": body_text[:2000],
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

    except Exception as e:
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()}


# ===== Confluence =====

@tool
def confluence_search_pages(query: str, limit: int = 10) -> dict:
    """Zoek naar Confluence-pagina's op basis van tekst."""
    try:
        q = (query or "").strip()
        if not q:
            return {"ok": False, "error": "query mag niet leeg zijn."}

        params = {
            "cql": f'text ~ "{q}"',
            "limit": max(1, min(limit, 25)),
            "expand": "space",
        }

        data = _conf_get("/rest/api/search", params=params)
        results = data.get("results", []) or []

        pages = []
        for r in results:
            content = r.get("content") or {}
            if content.get("type") != "page":
                continue
            page_id = content.get("id")
            title = content.get("title")
            space = (content.get("space") or {}).get("name")
            link = None
            if page_id and CONF_BASE_URL:
                link = f"{CONF_BASE_URL.rstrip('/')}/pages/{page_id}"

            pages.append(
                {
                    "id": page_id,
                    "title": title,
                    "space": space,
                    "url": link,
                }
            )

        return {"ok": True, "query": q, "pages": pages}

    except Exception as e:
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()}


@tool
def confluence_get_page(page_id: str, include_body: bool = True) -> dict:
    """Haal details en (optioneel) body van een Confluence-pagina op."""
    try:
        if not page_id:
            return {"ok": False, "error": "page_id mag niet leeg zijn."}

        expand = "version,space"
        if include_body:
            expand += ",body.storage"

        data = _conf_get(f"/rest/api/content/{page_id}", params={"expand": expand})

        title = data.get("title")
        space = (data.get("space") or {}).get("name")
        version = (data.get("version") or {}).get("number")
        link = None
        if CONF_BASE_URL:
            link = f"{CONF_BASE_URL.rstrip('/')}/pages/{page_id}"

        body_html = None
        if include_body:
            storage = (data.get("body") or {}).get("storage") or {}
            body_html = storage.get("value")

        if body_html and len(body_html) > 20000:
            body_html = body_html[:20000]

        return {
            "ok": True,
            "id": data.get("id"),
            "title": title,
            "space": space,
            "version": version,
            "url": link,
            "body_html": body_html,
        }

    except Exception as e:
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()}


# ---------------------------------------------------------------------------
# All tools list
# ---------------------------------------------------------------------------

all_tools = [
    # Tickets
    tickets_search,
    ticket_get,
    ticket_comments,
    ticket_add_internal_note,
    ticket_categorize,
    ticket_generate_draft,
    ticket_solution_rate,
    ticket_metrics,
    tickets_tag_stats,
    tickets_analyze,
    # KB
    kb_generate_draft,
    kb_search_articles,
    kb_create_draft_article,
    # Reporting
    tickets_export_csv,
    # General
    ping,
    # Jira
    jira_get_issue,
    # Confluence
    confluence_search_pages,
    confluence_get_page,
]


# ---------------------------------------------------------------------------
# ZAS Agent — built with LangChain
# ---------------------------------------------------------------------------

ZAS_SYSTEM_PROMPT = """\
BELANGRIJK: IDs VOOR KENNISBANKARTIKELEN
- Gebruik altijd:
- Permission ID = 295492
- Segment ID = 138711
- Section ID = 115000214091
- Als deze ontbreken: vraag eerst op met kb_list_permissions_and_segments.
Je bent de Zendesk Intelligence Agent.

Analyseer supportdata om trends, efficiëntie en ticketcategorieën te bepalen en \
kennisartikelen te schrijven.
Je neemt nooit contact op met klanten; alle output is intern.

TOOLS
- tickets_search – zoek tickets
- ticket_categorize – classificeer types
- ticket_solution_rate – meet oplossingsgraad
- ticket_generate_draft – maak KB-concept
- ticket_comments – lees ticketcontext
- ticket_add_internal_note – voeg interne notitie toe (Wanneer er een comment wordt \
toegevoegd aan een ticket zet er dan - Comment van ZAS <3 - bij)
- kb_search_articles – zoek bestaande KB's
- kb_create_draft_article – maak nieuw conceptartikel

GEBRUIK
- Bij een ticket analyse check meteen of er een oude ticket is met hetzelfde probleem + \
kennisbank artikelen die relevant kunnen zijn.
- Combineer tools logisch (bv. cluster → rate → draft).
- Gebruik add_internal_note voor inzichten: "Situatie… Analyse… Advies…".
- Controleer met kb_search_articles of het onderwerp al bestaat; maak anders een draft.
- Verwijder of maskeer PII met [REDACTED].
- Meld kort als een tool faalt en ga verder.
- Standaardquery: `status:solved created>2025-10-01`, limit 100.
- Voor relevante kennisbankartikelen geef je altijd de link (https://... zonder HTML \
markeringen!) naar de gevonden artikelen mee in jouw antwoord naar de support medewerker.
- Wanneer er gevraagd word om een interne comment te plaatsen, zet je je volledige analyse \
in de comment, beginnend met "Analyse door ZAS Agent:", gevolgd door je analyse over \
desbetreffende ticket.
- Als een ticket geparkeerd is en er staat een Jira-issue key in het ticket (bijv. in een \
custom veld of in de omschrijving), gebruik jira_get_issue om de status, toegewezen developer \
en laatste comments van het technische team op te halen en geef een begrijpelijke samenvatting \
aan de klant.
- Als je inhoudelijke uitleg nodig hebt over de werking van onze software, zoek dan eerst met \
confluence_search_pages op relevante zoektermen (feature, module, foutmelding, etc.) en gebruik \
daarna confluence_get_page om de inhoud te lezen. Vat deze informatie samen in je eigen woorden \
voor de klant, zonder ruwe HTML te tonen.

OUTPUT
- Wanneer er gevraagd word om een kennisbank concept te maken:
  Permission ID = 295492
  Segment ID = 138711
  Section ID = 115000214091
- Antwoord beknopt en professioneel in het Nederlands.
- Analytics → korte samenvatting + JSON.
- KB → HTML (PROBLEEM, OORZAAK, OPLOSSING, WANNEER ESCALEREN) + metadata-JSON.
  Voor kennisbankartikelen genereer je altijd HTML (geen Markdown), bijv.:
  <h2><strong>PROBLEEM</strong></h2><p>...</p>
  <h2><strong>OORZAAK</strong></h2><p>...</p>
  <h2><strong>OPLOSSING</strong></h2><p>...</p>
  <ol><li>Stap 1...</li><li>Stap 2...</li></ol>
  <h2><strong>WANNEER ESCALEREN</strong></h2><p>...</p>
  De string die je aan kb_create_draft_article.body meegeeft moet direct geldige HTML zijn.
  Gebruik geen Markdown-syntax zoals **vet**, _cursief_ of ![afbeelding](url).\
"""

# Model identifier: LangChain's init_chat_model resolves "openai:gpt-4.1-mini"
# to ChatOpenAI(model="gpt-4.1-mini"). You can also pass a ChatOpenAI instance.
ZAS_MODEL = os.getenv("ZAS_MODEL", "openai:gpt-4.1-mini")

zas_agent = create_agent(
    model=ZAS_MODEL,
    tools=all_tools,
    system_prompt=ZAS_SYSTEM_PROMPT,
    name="ZAS",
)


# ---------------------------------------------------------------------------
# Workflow API (optioneel)
# ---------------------------------------------------------------------------

class WorkflowInput(BaseModel):
    input_as_text: str


class WorkflowConfig(BaseModel):
    steps: List[Dict[str, Any]] = []


async def run_zas_workflow(
    workflow: Dict[str, Any],
    conversation_history: Optional[List[BaseMessage]] = None,
) -> Dict[str, Any]:
    if conversation_history is None:
        conversation_history = []

    workflow_input = WorkflowInput(**workflow.get("input", {}))
    workflow_config = WorkflowConfig(**workflow.get("config", {}))
    _ = workflow_config

    input_messages = [
        *conversation_history,
        HumanMessage(content=workflow_input.input_as_text),
    ]

    result = await zas_agent.ainvoke({"messages": input_messages})
    output_messages = result["messages"]

    reply_text = ""
    for msg in reversed(output_messages):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            reply_text = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    return {"output_text": reply_text}


# ---------------------------------------------------------------------------
# Chat-turn API – wordt aangeroepen door chat_api.py
# ---------------------------------------------------------------------------

async def run_zas_chat_turn(
    message: str,
    history: Optional[List[BaseMessage]] = None,
    tenant_id: Optional[str] = None,
    url: Optional[str] = None,
) -> tuple[str, List[BaseMessage]]:
    if history is None:
        history = []

    parts: list[str] = []
    if tenant_id:
        parts.append(f"[tenantId: {tenant_id}]")
    if url:
        parts.append(f"[pageUrl: {url}]")
    parts.append(message)

    user_text = "\n".join(parts)

    input_messages = [*history, HumanMessage(content=user_text)]

    result = await zas_agent.ainvoke({"messages": input_messages})
    updated_messages: List[BaseMessage] = result["messages"]

    reply_text = ""
    for msg in reversed(updated_messages):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            reply_text = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    return reply_text, updated_messages
