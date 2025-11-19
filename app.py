import os
import csv
import time
import math
import traceback
import requests
import pandas as pd
from dotenv import load_dotenv
from fastmcp import FastMCP

# 1) Laad .env uit dezelfde map als dit bestand (optioneel)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)  # als .env ontbreekt is dat geen fout; dan worden OS env-vars gebruikt

# 2) Lees env en valideer verplichte Zendesk-variabelen
# ---- ZENDESK ENV ----
ZD_SUB = os.getenv("ZENDESK_SUBDOMAIN")
ZD_EMAIL = os.getenv("ZENDESK_EMAIL")
ZD_TOKEN = os.getenv("ZENDESK_API_TOKEN")

# ---- JIRA ENV (optioneel, tools checken dit zelf) ----
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

# ---- CONFLUENCE ENV (optioneel, tools checken dit zelf) ----
CONF_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
CONF_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONF_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")

missing = []
for k in ("ZENDESK_SUBDOMAIN", "ZENDESK_EMAIL", "ZENDESK_API_TOKEN"):
    if not os.getenv(k):
        missing.append(k)

if missing:
    raise RuntimeError(
        f"Ontbrekende verplichte Zendesk env vars: {missing}. "
        f"Zet ze als environment variable of in {ENV_PATH}."
    )

AUTH = (f"{ZD_EMAIL}/token", ZD_TOKEN)
BASE = f"https://{ZD_SUB}.zendesk.com/api/v2"

# 3) MCP server
mcp = FastMCP(name="zendesk_mcp_http")

# ---------- helpers ----------
def _get(url_path, params=None, timeout=20):
    url = f"{BASE}{url_path}"
    r = requests.get(url, params=params or {}, auth=AUTH, timeout=timeout)
    r.raise_for_status()
    return r.json()

def _put(url_path, payload, timeout=20):
    """
    Algemene helper voor PUT-requests naar de Zendesk API.
    - url_path: bv. "/tickets/123.json"
    - payload: dict die als JSON body wordt verstuurd
    """
    url = f"{BASE}{url_path}"
    r = requests.put(url, json=payload, auth=AUTH, timeout=timeout)
    r.raise_for_status()
    return r.json()

def _post(url_path, payload, timeout=20):
    """
    Algemene helper voor POST-requests naar de Zendesk API.
    """
    url = f"{BASE}{url_path}"
    r = requests.post(url, json=payload, auth=AUTH, timeout=timeout)
    r.raise_for_status()
    return r.json()

def _paginate_search(query: str, limit: int):
    """
    Loopt /search.json pagina's af tot 'limit' is bereikt of er geen data meer is.
    """
    results = []
    page = 1
    per_page = min(100, max(1, limit))
    while len(results) < limit:
        data = _get("/search.json", {"query": query, "page": page, "per_page": per_page})
        batch = [x for x in data.get("results", []) if x.get("result_type") == "ticket"]
        results.extend(batch)
        if not data.get("next_page") or len(batch) == 0:
            break
        page += 1
        # kleine pauze i.v.m. rate limits
        time.sleep(0.15)
    return results[:limit]

# ---------- JIRA HELPERS ----------
def _jira_get(path: str, params=None, timeout: int = 20):
    """
    Kleine helper om Jira REST API te benaderen.
    path: bv. "/rest/api/3/issue/KEY-123"
    """
    if not (JIRA_BASE_URL and JIRA_EMAIL and JIRA_API_TOKEN):
        raise RuntimeError(
            "Jira ENV ontbreekt: zet JIRA_BASE_URL, JIRA_EMAIL en JIRA_API_TOKEN in .env"
        )
    url = f"{JIRA_BASE_URL.rstrip('/')}{path}"
    r = requests.get(
        url,
        params=params or {},
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()


# ---------- CONFLUENCE HELPERS ----------
def _conf_get(path: str, params=None, timeout: int = 20):
    """
    Helper voor Confluence REST API.
    path: bv. "/rest/api/content/12345"
    """
    if not (CONF_BASE_URL and CONF_EMAIL and CONF_API_TOKEN):
        raise RuntimeError(
            "Confluence ENV ontbreekt: zet CONFLUENCE_BASE_URL, CONFLUENCE_EMAIL en CONFLUENCE_API_TOKEN in .env"
        )
    url = f"{CONF_BASE_URL.rstrip('/')}{path}"
    r = requests.get(
        url,
        params=params or {},
        auth=(CONF_EMAIL, CONF_API_TOKEN),
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()

# ---------- BASIS TEST TOOL ----------
@mcp.tool
def ping() -> str:
    """Controleer of MCP actief is."""
    return "pong"

# ---------- DEBUG: ENV VARS ----------
@mcp.tool
def debug_env_sources():
    """DEBUG: laat zien welke Jira/Confluence env-waarden de server ziet."""
    return {
        "JIRA_BASE_URL": JIRA_BASE_URL,
        "JIRA_EMAIL": JIRA_EMAIL,
        "has_JIRA_TOKEN": bool(JIRA_API_TOKEN),
        "CONF_BASE_URL": CONF_BASE_URL,
        "CONF_EMAIL": CONF_EMAIL,
        "has_CONF_TOKEN": bool(CONF_API_TOKEN),
    }

# ---------- ZOEKEN (verbeterde variant) ----------
@mcp.tool
def tickets_search(query: str, limit: int = 50):
    """
    Zoek Zendesk tickets met Zendesk zoeksyntaxis.
    Voorbeeld: 'type:ticket status<solved created>2025-01-01'
    Returns: count + subset velden.
    """
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


# ---------- DETAILS VAN 1 TICKET ----------
@mcp.tool
def ticket_get(ticket_id: int):
    """
    Haal volledige ticketdetails op.
    """
    try:
        data = _get(f"/tickets/{ticket_id}.json")
        return {"ok": True, "ticket": data.get("ticket")}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}


# ---------- COMMENTS / CONVERSATION ----------
@mcp.tool
def ticket_comments(ticket_id: int, include_public: bool = True):
    """
    Haal alle comments (publiek + intern) op. Filter op public wanneer gewenst.
    """
    try:
        data = _get(f"/tickets/{ticket_id}/comments.json")
        comments = data.get("comments", [])
        if include_public:
            comments = [c for c in comments if c.get("public", False)]
        return {"ok": True, "count": len(comments), "comments": comments}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}

# ----------- INTERNE OPMERKINGEN -------------
@mcp.tool
def ticket_add_internal_note(ticket_id: int, body: str):
    """
    Voeg een *interne opmerking* (private comment) toe aan een Zendesk-ticket.

    - De opmerking is NIET zichtbaar voor de requester, alleen voor agents.
    - Wordt opgeslagen als een gewone ticketcomment met `public = false`.
    """
    try:
        text = (body or "").strip()
        if not text:
            return {
                "ok": False,
                "error": "De body van de interne opmerking mag niet leeg zijn."
            }

        # Payload volgens Zendesk Tickets API:
        # PUT /api/v2/tickets/{id}.json
        # { "ticket": { "comment": { "body": "...", "public": false } } }
        payload = {
            "ticket": {
                "comment": {
                    "body": text,
                    "public": False
                }
            }
        }

        api_response = _put(f"/tickets/{ticket_id}.json", payload)

        # Optioneel: laatste comment ophalen als snelle check/preview
        latest_body = None
        try:
            comments_data = _get(f"/tickets/{ticket_id}/comments.json")
            comments = comments_data.get("comments", [])
            if comments:
                latest_body = comments[-1].get("body")
        except Exception:
            # Geen hard error als de controle-call faalt
            pass

        return {
            "ok": True,
            "ticket_id": ticket_id,
            "internal_note_preview": latest_body,
            "raw_api_response": api_response,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "trace": traceback.format_exc()
        }


# ---------- TICKET CLUSTER TOPICS ----------
@mcp.tool
def ticket_cluster_topics(query: str, limit: int = 300, n_clusters: int = 8):
    """
    Maak clusters van veelvoorkomende ticketonderwerpen.
    Gebruik dit om te ontdekken welke problemen het vaakst voorkomen.

    Args:
        query: Zendesk zoekquery, bijv. "status:solved created>2025-10-01"
        limit: max aantal tickets om te analyseren
        n_clusters: gewenste aantal thema-groepen
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import KMeans
        tickets = _paginate_search(query=query, limit=limit)
        subjects = [t.get("subject") or "" for t in tickets]
        if not subjects:
            return {"ok": True, "clusters": [], "note": "No subjects found"}
        vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
        X = vectorizer.fit_transform(subjects)
        k = min(max(1, n_clusters), len(subjects))
        km = KMeans(n_clusters=k, n_init="auto").fit(X)
        buckets = {}
        for idx, label in enumerate(km.labels_):
            buckets.setdefault(int(label), []).append(subjects[idx])
        clusters = [
            {"cluster": cid, "count": len(subj), "examples": subj[:5]}
            for cid, subj in sorted(buckets.items(), key=lambda kv: len(kv[1]), reverse=True)
        ]
        return {"ok": True, "clusters": clusters, "total_tickets": len(subjects)}
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}

# ---------- CATEGORIZE ----------
@mcp.tool
def ticket_categorize(query: str, limit: int = 300):
    """
    Ken een categorie toe aan elk ticket (heuristisch).
    Handig voor routing en volumestatistiek per categorie.
    """
    try:
        tickets = _paginate_search(query=query, limit=limit)
        categories = {
            "login": ["login","password","2fa","two factor","authentication","auth code","verify code"],
            "billing": ["invoice","payment","refund","charged","billing","credit card"],
            "bug": ["error","crash","not working","broken","fails","issue","bug"],
            "feature": ["feature request","can you add","improvement","roadmap"],
            "account": ["deactivate account","delete account","account access","subscription","upgrade plan"],
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
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}

# ---------- GENERATE DRAFT ----------
@mcp.tool
def ticket_generate_draft(query: str, limit: int = 20):
    """
    Bundel opgeloste tickets over hetzelfde probleem zodat de agent daar een KB-artikel uit kan schrijven.

    Werkwijze:
    - Zoekt tickets met jouw query + status:solved
    - Haalt publieke comments op (geen private comments)
    - Bouwt samenvattende context per ticket
    """
    try:
        import time
        solved_query = query if "status:" in query else f"{query} status:solved"
        tickets = _paginate_search(query=solved_query, limit=limit)
        bundle = []
        for t in tickets:
            tid = t.get("id")
            subject = t.get("subject") or ""
            try:
                raw_comments = _get(f"/tickets/{tid}/comments.json").get("comments", [])
                public_comments = [c.get("body","") for c in raw_comments if c.get("public", False)]
            except Exception:
                public_comments = []
            summarized = ""
            if public_comments:
                first = public_comments[0].strip().replace("\r"," ").replace("\n"," ")
                summarized = (first[:220] + "...") if len(first) > 220 else first
            bundle.append({"id": tid, "subject": subject, "problem_summary": summarized})
            time.sleep(0.1)
        lines = [f"- Ticket {b['id']} :: '{b['subject']}' :: Mogelijk probleem: {b['problem_summary']}" for b in bundle]
        combined_text = "Deze tickets lijken over hetzelfde of vergelijkbare probleem te gaan.\nGebruik dit om een KB-artikel te schrijven met secties: PROBLEEM / OORZAAK / OPLOSSING (STAPPEN) / WANNEER ESCALEREN.\n\n" + "\n".join(lines)
        return {"ok": True, "tickets_used": len(bundle), "draft_context": combined_text[:10000], "hint": "Gebruik dit om een kennisbankartikel te schrijven."}
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}

# ---------- SOLUTION RATE ----------
@mcp.tool
def ticket_solution_rate(query: str, limit: int = 200):
    """
    Meet hoe vaak tickets direct opgelost worden zonder reopen.
    We kijken voor elk ticket naar metrics:
      - reopens
      - replies
      - status
    Een ticket telt als 'direct_solved' als:
      - status == solved
      - reopens == 0
      - replies <= 1
    """
    try:
        import time
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
        return {"ok": True, "total": total, "directly_solved": direct, "reopened": reopened_any, "direct_resolution_rate_pct": round(rate, 1)}
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}


# ---------- METRICS / SLA ----------
@mcp.tool
def ticket_metrics(ticket_id: int):
    """
    Haal ticket metrics op (o.a. first/full resolution, requester/agent wait times) indien beschikbaar.
    """
    try:
        data = _get(f"/tickets/{ticket_id}/metrics.json")
        return {"ok": True, "metrics": data.get("ticket_metric")}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}


# ---------- TAG / STATUS / ASSIGNEE STATISTIEKEN ----------
@mcp.tool
def tickets_tag_stats(query: str, limit: int = 200):
    """
    Aggegreer top-tags, statussen en assignees over gevonden tickets.
    """
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

        # Top N sorteringen
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

# ---------- Kennisbank Generatie ----------
@mcp.tool
def kb_generate_draft(query: str, limit: int = 20):
    """
    Genereert concept kennisbank-artikel op basis van opgeloste tickets.
    (Deze tool bundelt data; de LLM-agent maakt de uiteindelijke tekst.)
    """
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
            "draft_context": combined_text[:10000],  # beperkt voor LLM context
            "hint": "Gebruik deze context in de agent om een kennisbankartikel te schrijven.",
        }
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}

# ---------- END-TO-END ANALYSE ----------
@mcp.tool
def tickets_analyze(
    query: str,
    limit: int = 200,
    enrich_with_metrics: bool = True,
    metrics_sample: int = 50
):
    """
    End-to-end analyse: zoekt tickets (limit), berekent verdelingen, en (optioneel)
    haalt metrics op voor een deel-steekproef (metrics_sample) om doorlooptijden/SLA te schatten.

    Let op: metrics ophalen per ticket kan trager zijn en rate-limited worden; daarom 'metrics_sample'.
    """
    try:
        tickets = _paginate_search(query=query, limit=limit)
        if not tickets:
            return {"ok": True, "summary": {"total": 0}, "insights": {}}

        # basis aggregaties
        def _inc(d, k): d.__setitem__(k, d.get(k, 0) + 1)

        by_status, by_priority, by_assignee, tag_counts = {}, {}, {}, {}
        for t in tickets:
            _inc(by_status, t.get("status") or "unknown")
            _inc(by_priority, t.get("priority") or "none")
            _inc(by_assignee, str(t.get("assignee_id") or "unassigned"))
            for tag in t.get("tags", []) or []:
                _inc(tag_counts, tag)

        # metrics (steekproef)
        metrics_rows = []
        if enrich_with_metrics:
            sample_ids = [t["id"] for t in tickets[:max(0, min(metrics_sample, len(tickets)))]]
            for tid in sample_ids:
                try:
                    m = _get(f"/tickets/{tid}/metrics.json").get("ticket_metric", {})
                except Exception:
                    m = {}
                # normalize minutenvelden (kunnen objecten zijn met 'calendar'/'business')
                def _mins(x):
                    if isinstance(x, dict):
                        # pak beide als beschikbaar
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
                time.sleep(0.1)  # rate-limit vriendelijk

        # compacte statistieken uit metrics_rows
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
                if not vs: return {}
                vs_sorted = sorted(vs)
                n = len(vs_sorted)
                p50 = vs_sorted[n//2] if n % 2 else (vs_sorted[n//2 - 1] + vs_sorted[n//2]) / 2
                p90 = vs_sorted[math.floor(0.9*(n-1))]
                return {"n": n, "mean": sum(vs_sorted)/n, "p50": p50, "p90": p90}

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
            "sample_metrics": metrics_rows[:5],  # klein voorbeeld
        }

    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}

# ---------- JIRA: ISSUE DETAILS ----------
@mcp.tool
def jira_get_issue(issue_key: str, max_comments: int = 5):
    """
    Haal details op van een Jira-issue (bv. 'TGR-123') inclusief laatste comments.
    
    Handig voor:
    - geparkeerde Zendesk-tickets die een gekoppeld Jira-issue hebben
    - status + updates van het technische team
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

# ---------- CONFLUENCE: SEARCH ----------
@mcp.tool
def confluence_search_pages(query: str, limit: int = 10):
    """
    Zoek naar Confluence-pagina's op basis van tekst.

    Returns een lijst met paginatitel, id en link.
    """
    try:
        q = (query or "").strip()
        if not q:
            return {"ok": False, "error": "query mag niet leeg zijn."}

        # CQL: text~"zoekterm"
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
            # self-link / webLink
            link = None
            for l in content.get("_links", {}).values():
                # _links bevat bv. "webui"; de volledige base zit in CONF_BASE_URL
                # we bouwen zelf een URL met base
                pass
            # Simpele benadering: gebruik CONF_BASE_URL + "/pages/" + id
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

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        return {
            "ok": False,
            "error": f"HTTPError bij Confluence search (status {status})",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()}

# ---------- CONFLUENCE: PAGE DETAILS ----------
@mcp.tool
def confluence_get_page(page_id: str, include_body: bool = True):
    """
    Haal details en (optioneel) body van een Confluence-pagina op.

    - page_id: ID van de pagina (string)
    """
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

        # De agent kan HTML prima verwerken, maar we beperken de lengte wat
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

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        return {
            "ok": False,
            "error": f"HTTPError bij Confluence page {page_id} (status {status})",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()}

# ---------- KENNISBANK: SEARCH ----------
@mcp.tool
def kb_search_articles(
    query: str,
    limit: int = 20,
    label_names: str = "",
    locale: str = ""
):
    """
    Zoek in Zendesk Help Center-artikelen (kennisbank).

    - query: vrije zoektekst (titel/body/labels)
    - limit: max aantal resultaten (max 100)
    - label_names: optioneel, komma-gescheiden labels (bv. "2fa,login")
    - locale: optioneel filter op locale (bv. "nl" / "nl-nl"); wordt client-side gefilterd
    """
    try:
        q = (query or "").strip()
        if not q and not label_names:
            return {
                "ok": False,
                "error": "Geef minimaal een query of label_names op."
            }

        per_page = min(100, max(1, limit))
        params = {
            "per_page": per_page,
        }
        if q:
            params["query"] = q
        if label_names:
            params["label_names"] = label_names

        # Zendesk: GET /api/v2/help_center/articles/search
        data = _get("/help_center/articles/search.json", params)
        raw_results = data.get("results", [])

        # optioneel: filter op locale
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

# ---------- KENNISBANK: CREATE DRAFT ----------
@mcp.tool
def kb_create_draft_article(
    section_id=None,
    title: str = "",
    body: str = "",
    locale: str = "nl",
    permission_group_id: int = None,
    user_segment_id: int = None,
):
    try:
        import os
        import traceback

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

        sid_source = section_id if section_id not in (None, "", 0) else os.getenv("ZENDESK_KB_CONCEPT_SECTION_ID")
        if not sid_source:
            return {
                "ok": False,
                "error": (
                    "Geen geldige section_id opgegeven en ZENDESK_KB_CONCEPT_SECTION_ID ontbreekt. "
                    "Zet deze env var of geef een section_id mee."
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
        import traceback
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()}

# ---------- KENNISBANK: PERMISSIONS EN SEGMENTS LISTEN ----------
@mcp.tool
def kb_list_permissions_and_segments(include_built_in: bool = True):
    """
    Haalt de lijst op van Guide management permission groups en Help Center user segments.

    Handig om de juiste IDs te vinden voor:
    - permission_group_id (bij artikelen)
    - user_segment_id (wie mag het artikel zien)
    """
    try:
        import traceback

        # 1) Permission groups (beheer-rechten voor artikelen)
        #
        # API: GET /api/v2/guide/permission_groups.json
        # BASE = "https://{subdomain}.zendesk.com/api/v2"
        pg_raw = _get("/guide/permission_groups.json")

        permission_groups = pg_raw.get("permission_groups", pg_raw)
        pg_simplified = [
            {
                "id": pg.get("id"),
                "name": pg.get("name"),
                "built_in": pg.get("built_in"),
            }
            for pg in permission_groups
        ]

        # 2) User segments (welke users/agents content mogen zien)
        #
        # API: GET /api/v2/help_center/user_segments.json
        params = {}
        if not include_built_in:
            # Alleen custom user segments
            params["built_in"] = False

        us_raw = _get("/help_center/user_segments.json", params=params)
        user_segments = us_raw.get("user_segments", us_raw)
        us_simplified = [
            {
                "id": us.get("id"),
                "name": us.get("name"),
                "user_type": us.get("user_type"),
                "built_in": us.get("built_in"),
            }
            for us in user_segments
        ]

        return {
            "ok": True,
            "permission_groups": pg_simplified,
            "user_segments": us_simplified,
        }

    except Exception as e:
        import traceback
        return {
            "ok": False,
            "error": str(e),
            "trace": traceback.format_exc(),
        }


# ---------- EXPORT ----------
@mcp.tool
def tickets_export_csv(query: str, path: str = "tickets_export.csv", limit: int = 1000):
    """
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