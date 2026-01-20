# tools_confluence.py - tools voor Confluence

from src.zas.core.helpers import mcp, _conf_get
import os
import traceback
import requests

# ---- CONFLUENCE ENV ----
CONF_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
CONF_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONF_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")


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
