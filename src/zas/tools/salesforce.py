# tools_salesforce.py - Salesforce session management tools

import os
from datetime import datetime, timedelta

import requests
from src.zas.core.database import (
	SessionLocal,
	get_salesforce_oauth_credentials,
	get_salesforce_session,
	list_salesforce_sessions,
	set_salesforce_oauth_credentials,
	set_salesforce_session,
)

from src.zas.core.helpers import mcp

DEFAULT_LOGIN_URL = os.getenv("SALESFORCE_LOGIN_URL", "https://login.salesforce.com")
API_VERSION = os.getenv("SALESFORCE_API_VERSION", "v61.0")
READ_ONLY = os.getenv("ZAS_SF_READ_ONLY", "true").lower() in ("1", "true", "yes")


@mcp.tool
def salesforce_session_store(
	organisation_id: str,
	access_token: str,
	instance_url: str,
	refresh_token: str | None = None,
	expires_at: str | None = None,
):
	"""Bewaar of update een Salesforce sessie voor een organisatie.

	- organisation_id: key uit de organisations tabel
	- access_token / refresh_token: OAuth tokens
	- instance_url: bv. https://mydomain.my.salesforce.com
	- expires_at: ISO8601 tijdstip waarop access_token verloopt (optioneel)
	"""
	if READ_ONLY:
		return {"ok": False, "error": "salesforce tools are read-only"}

	expires_dt = None
	if expires_at:
		try:
			expires_dt = datetime.fromisoformat(expires_at)
		except Exception:
			return {"ok": False, "error": "expires_at must be ISO8601"}

	with SessionLocal() as db:
		try:
			set_salesforce_session(
				db,
				organisation_id=organisation_id,
				access_token=access_token,
				instance_url=instance_url,
				refresh_token=refresh_token,
				expires_at=expires_dt,
			)
			return {"ok": True}
		except Exception as e:
			return {"ok": False, "error": str(e)}


@mcp.tool
def salesforce_session_get(organisation_id: str):
	"""Haal de opgeslagen Salesforce sessie op voor een organisatie (auto-refresh indien nodig)."""
	result = _get_or_refresh_session(organisation_id)
	return result


@mcp.tool
def salesforce_sessions_list():
	"""Toon alle bekende Salesforce sessies (zonder tokens in de lijst)."""
	with SessionLocal() as db:
		return list_salesforce_sessions(db)


@mcp.tool
def salesforce_oauth_set_credentials(
	organisation_id: str,
	client_id: str,
	client_secret: str,
	refresh_token: str,
	instance_url: str | None = None,
	expires_at: str | None = None,
):
	"""Sla OAuth client + refresh token op voor een organisatie."""
	if READ_ONLY:
		return {"ok": False, "error": "salesforce tools are read-only"}
	expires_dt = None
	if expires_at:
		try:
			expires_dt = datetime.fromisoformat(expires_at)
		except Exception:
			return {"ok": False, "error": "expires_at must be ISO8601"}

	with SessionLocal() as db:
		try:
			set_salesforce_oauth_credentials(
				db,
				organisation_id=organisation_id,
				client_id=client_id,
				client_secret=client_secret,
				refresh_token=refresh_token,
				instance_url=instance_url,
				expires_at=expires_dt,
			)
			return {"ok": True}
		except Exception as e:
			return {"ok": False, "error": str(e)}


@mcp.tool
def salesforce_oauth_authorize_url(
	client_id: str,
	redirect_uri: str,
	state: str | None = None,
	login_url: str | None = None,
):
	"""Genereer de Salesforce OAuth authorize URL (gebruiker moet deze in browser openen)."""
	if READ_ONLY:
		return {"ok": False, "error": "salesforce tools are read-only"}
	base = (login_url or DEFAULT_LOGIN_URL).rstrip("/")
	params = [
		("response_type", "code"),
		("client_id", client_id),
		("redirect_uri", redirect_uri),
		("scope", "refresh_token offline_access api"),
	]
	if state:
		params.append(("state", state))
	query = "&".join([f"{k}={requests.utils.quote(str(v))}" for k, v in params])
	return {"authorize_url": f"{base}/services/oauth2/authorize?{query}"}


@mcp.tool
def salesforce_oauth_exchange_code(
	organisation_id: str,
	client_id: str,
	client_secret: str,
	code: str,
	redirect_uri: str,
	login_url: str | None = None,
):
	"""Wissel een auth code om voor refresh/access tokens en sla ze op."""
	if READ_ONLY:
		return {"ok": False, "error": "salesforce tools are read-only"}
	base = (login_url or DEFAULT_LOGIN_URL).rstrip("/")
	url = f"{base}/services/oauth2/token"
	data = {
		"grant_type": "authorization_code",
		"code": code,
		"client_id": client_id,
		"client_secret": client_secret,
		"redirect_uri": redirect_uri,
	}
	try:
		resp = requests.post(url, data=data, timeout=30)
		resp.raise_for_status()
		payload = resp.json()
	except Exception as e:
		return {"ok": False, "error": f"token exchange failed: {e}"}

	refresh_token = payload.get("refresh_token")
	access_token = payload.get("access_token")
	instance_url = payload.get("instance_url")
	expires_in = payload.get("expires_in")
	if not refresh_token or not access_token or not instance_url:
		return {
			"ok": False,
			"error": "token response missing refresh_token/access_token/instance_url",
		}

	expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in)) if expires_in else None

	with SessionLocal() as db:
		try:
			set_salesforce_oauth_credentials(
				db,
				organisation_id=organisation_id,
				client_id=client_id,
				client_secret=client_secret,
				refresh_token=refresh_token,
				instance_url=instance_url,
			)
			set_salesforce_session(
				db,
				organisation_id=organisation_id,
				access_token=access_token,
				refresh_token=refresh_token,
				instance_url=instance_url,
				expires_at=expires_at,
			)
			return {
				"ok": True,
				"instance_url": instance_url,
				"expires_at": expires_at.isoformat() if expires_at else None,
			}
		except Exception as e:
			return {"ok": False, "error": str(e)}


def _get_or_refresh_session(organisation_id: str):
	"""Return a valid session, refreshing via stored OAuth credentials if needed."""
	now = datetime.utcnow()
	with SessionLocal() as db:
		row = get_salesforce_session(db, organisation_id)
		if row and (row.expires_at is None or row.expires_at > now + timedelta(seconds=60)):
			return {
				"ok": True,
				"organisation_id": row.organisation_id,
				"instance_url": row.instance_url,
				"access_token": row.access_token,
				"refresh_token": row.refresh_token,
				"issued_at": row.issued_at.isoformat() if row.issued_at else None,
				"expires_at": row.expires_at.isoformat() if row.expires_at else None,
			}

		cred = get_salesforce_oauth_credentials(db, organisation_id)
		if not cred:
			return {"ok": False, "error": "no oauth credentials stored for organisation"}

		refresh_token = cred.refresh_token
		if not refresh_token:
			return {"ok": False, "error": "no refresh token available"}

		login_url = cred.instance_url or DEFAULT_LOGIN_URL
		base = login_url.rstrip("/")
		url = f"{base}/services/oauth2/token"
		data = {
			"grant_type": "refresh_token",
			"client_id": cred.client_id,
			"client_secret": cred.client_secret,
			"refresh_token": refresh_token,
		}
		try:
			resp = requests.post(url, data=data, timeout=30)
			resp.raise_for_status()
			payload = resp.json()
		except Exception as e:
			return {"ok": False, "error": f"refresh failed: {e}"}

		access_token = payload.get("access_token")
		instance_url = payload.get("instance_url") or cred.instance_url
		expires_in = payload.get("expires_in")
		new_refresh = payload.get("refresh_token") or refresh_token
		if not access_token or not instance_url:
			return {"ok": False, "error": "refresh response missing access_token/instance_url"}

		expires_at = now + timedelta(seconds=int(expires_in)) if expires_in else None
		try:
			set_salesforce_session(
				db,
				organisation_id=organisation_id,
				access_token=access_token,
				refresh_token=new_refresh,
				instance_url=instance_url,
				expires_at=expires_at,
			)
			expires_str = expires_at.isoformat() if expires_at else None
			return {
				"ok": True,
				"organisation_id": organisation_id,
				"instance_url": instance_url,
				"access_token": access_token,
				"refresh_token": new_refresh,
				"issued_at": datetime.utcnow().isoformat(),
				"expires_at": expires_str,
			}
		except Exception as e:
			return {"ok": False, "error": str(e)}


@mcp.tool
def salesforce_query(organisation_id: str, soql: str):
	"""Voer een read-only SOQL query uit tegen Salesforce.

	Requires a stored session for the organisation; auto-refresh will be attempted.
	Returns records only; does not perform any writes.
	"""
	soql = (soql or "").strip()
	if not organisation_id:
		return {"ok": False, "error": "organisation_id is required"}
	if not soql:
		return {"ok": False, "error": "soql is required"}

	# Get a valid session (may refresh via stored credentials)
	res = _get_or_refresh_session(organisation_id)
	if not res.get("ok"):
		return res

	access_token = res.get("access_token")
	instance_url = res.get("instance_url")
	if not access_token or not instance_url:
		return {"ok": False, "error": "missing access token or instance url"}

	url = f"{instance_url.rstrip('/')}/services/data/{API_VERSION}/query"
	params = {"q": soql}
	headers = {"Authorization": f"Bearer {access_token}"}
	try:
		resp = requests.get(url, params=params, headers=headers, timeout=30)
		resp.raise_for_status()
		payload = resp.json()
		# Return only read-only data fields
		return {
			"ok": True,
			"totalSize": payload.get("totalSize"),
			"done": payload.get("done"),
			"records": payload.get("records", []),
		}
	except Exception as e:
		return {"ok": False, "error": f"sf query failed: {e}"}
