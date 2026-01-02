from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse


def _extract_client_ip(request: Request) -> str:
	fwd = request.headers.get("x-forwarded-for")
	if fwd:
		return fwd.split(",")[0].strip()
	return request.client.host if request.client else "unknown"


def _is_authorized(user_id: Optional[str], org_id: Optional[str]) -> bool:
	# check if user_id and org_id are set.
	if not user_id or not org_id:
		return False
	# TODO; replace with DB-backed auth when ready.
	return True


def setup_middleware(app, logger):
	@app.middleware("http")
	async def log_and_auth(request: Request, call_next):
		client_ip = _extract_client_ip(request)
		user_id = request.headers.get("X-Salesforce-User-Id")
		org_id = request.headers.get("X-Salesforce-Org-Id")

		logger.info(
			"HTTP %s %s ip=%s user=%s org=%s",
			request.method,
			request.url.path,
			client_ip,
			user_id,
			org_id,
		)

		if not _is_authorized(user_id, org_id):
			return JSONResponse({"authorized": False}, status_code=403)

		return await call_next(request)

	return app
