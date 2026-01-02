# tools_kb.py - tools voor kennisbank


from core import mcp, _get, _post, _paginate_search
import os
import traceback

# =====================================================
# TOOLS: KENNISBANK — gebruikt door: KB-Agent
# =====================================================

@mcp.tool
def kb_generate_draft(query: str, limit: int = 20):
	"""[KB-Agent]

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
def kb_search_articles(
	query: str,
	limit: int = 20,
	label_names: str = "",
	locale: str = ""
):
	"""[KB-Agent]

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

# ---------- EXPORT ----------
