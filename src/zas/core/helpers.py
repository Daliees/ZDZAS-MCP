# core.py - centrale config, env en helpers voor MCP
import os
import time

import requests
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
mcp = FastMCP(
	name="zendesk_mcp_http",
)


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
