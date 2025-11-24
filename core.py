# core.py - centrale config, env en helpers voor MCP
import os
import csv
import time
import math
import traceback
import requests
import pandas as pd
from dotenv import load_dotenv
from fastmcp import FastMCP

# 1) Laad .env met expliciet pad
ENV_PATH = "/Users/dalil/zendesk-mcp-server/.env"
load_dotenv(ENV_PATH)

# 2) Lees env en valideer
ZD_SUB = os.getenv("ZENDESK_SUBDOMAIN")
ZD_EMAIL = os.getenv("ZENDESK_EMAIL")
ZD_TOKEN = os.getenv("ZENDESK_API_TOKEN")

missing = []
for k in ("ZENDESK_SUBDOMAIN", "ZENDESK_EMAIL", "ZENDESK_API_TOKEN"):
    if not os.getenv(k):
        missing.append(k)
if missing:
    raise RuntimeError(
        f"Ontbrekende env vars in .env: {missing}. Check {ENV_PATH}"
    )

AUTH = (f"{ZD_EMAIL}/token", ZD_TOKEN)
BASE = f"https://{ZD_SUB}.zendesk.com/api/v2"

# 3) MCP server en tools
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


# ---------- BASIS TEST TOOL ----------
