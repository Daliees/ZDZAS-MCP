# tools_ticket.py - tools voor tickets


from core import mcp, _get, _put, _paginate_search
import math
import time
import traceback


# =====================================================
# TOOLS: TICKETS — gebruikt door: Ticket-Agent
# =====================================================

@mcp.tool
def tickets_search(query: str, limit: int = 50):
    """[General-Agent]

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
    """[Ticket-Agent]

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
    """[Ticket-Agent]

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
    """[Ticket-Agent]

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
    """[Ticket-Agent]

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
    """[Ticket-Agent]

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
    """[Ticket-Agent]

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
    """[Ticket-Agent]

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
    """[Ticket-Agent]

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
    """[Ticket-Agent]

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
def tickets_analyze(
    query: str,
    limit: int = 200,
    enrich_with_metrics: bool = True,
    metrics_sample: int = 50
):
    """[Ticket-Agent]

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

# ---------- KENNISBANK: SEARCH ----------
