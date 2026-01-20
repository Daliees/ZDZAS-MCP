import json
import os
import uuid
from datetime import datetime

from agents import TResponseInputItem
from db import RequestLog, SessionLocal, upsert_entities
from fastapi import APIRouter, Body, Header, HTTPException

from zas_agent import run_zas_chat_turn

from .logging_utils import write_jsonl
from .schemas import ChatRequest, ChatResponse, FeedbackItem, ResetRequest


def create_router(
	logger,
	structured_log_path: str,
	feedback_log_path: str,
	conversation_histories: dict[str, list[TResponseInputItem]],
):
	router = APIRouter()

	@router.get("/ping")
	async def ping():
		return True

	@router.post("/chat", response_model=ChatResponse)
	async def chat(
		req: ChatRequest,
		x_zas_tenant_id: str | None = Header(None),
		x_zas_url: str | None = Header(None),
		x_session_id: str | None = Header(None),
		x_salesforce_org_id: str | None = Header(None, alias="X-Salesforce-Org-Id"),
		x_salesforce_user_id: str | None = Header(None, alias="X-Salesforce-User-Id"),
	):
		request_id = str(uuid.uuid4())

		tenant_id = req.tenantId or x_zas_tenant_id
		url = req.url or x_zas_url
		conv_id = req.conversationId or x_session_id or str(uuid.uuid4())
		org_id = (
			req.salesforceContext.orgId if req.salesforceContext else None
		) or x_salesforce_org_id
		user_id = (
			req.salesforceContext.userId if req.salesforceContext else None
		) or x_salesforce_user_id
		user_name = req.salesforceContext.userName if req.salesforceContext else None
		org_name = None
		history = conversation_histories.get(conv_id, [])

		logger.info(
			"CHAT request request_id=%s conv_id=%s tenant=%s user_id=%s message_len=%d history_len=%d",
			request_id,
			conv_id,
			tenant_id,
			user_id,
			len(req.message),
			len(history),
		)

		write_jsonl(
			structured_log_path,
			{
				"event": "chat_request",
				"requestId": request_id,
				"conversationId": conv_id,
				"tenantId": tenant_id,
				"url": url,
				"message": req.message,
				"salesforceContext": {
					"orgId": req.salesforceContext.orgId if req.salesforceContext else None,
					"userId": req.salesforceContext.userId if req.salesforceContext else None,
					"userName": req.salesforceContext.userName if req.salesforceContext else None,
					"userEmail": req.salesforceContext.userEmail if req.salesforceContext else None,
				},
				"headers": {
					"X-Salesforce-Org-Id": x_salesforce_org_id,
					"X-Salesforce-User-Id": x_salesforce_user_id,
					"X-Session-Id": x_session_id,
					"X-Zas-Tenant-Id": x_zas_tenant_id,
					"X-Zas-Url": x_zas_url,
				},
				"timestamp": datetime.now().isoformat(),
			},
		)

		try:
			reply_text, updated_history, tokens_used = await run_zas_chat_turn(
				message=req.message,
				history=history,
				tenant_id=tenant_id,
				url=url,
				user_id=user_id,
				org_id=org_id,
			)

		except PermissionError as e:
			logger.warning(
				"Unauthorized tool invocation request_id=%s user_id=%s org_id=%s",
				request_id,
				user_id,
				org_id,
			)
			write_jsonl(
				structured_log_path,
				{
					"event": "chat_unauthorized",
					"requestId": request_id,
					"conversationId": conv_id,
					"userId": user_id,
					"orgId": org_id,
					"timestamp": datetime.now().isoformat(),
				},
			)
			raise HTTPException(status_code=403, detail="Unauthorized") from e

		except Exception as e:
			logger.exception("Unhandled error on /chat request_id=%s", request_id)
			try:
				with SessionLocal() as db:
					upsert_entities(
						db,
						organisation_id=org_id,
						organisation_name=org_name,
						user_id=user_id,
						user_name=user_name,
						organisation_url=url,
					)
					error_log = RequestLog(
						request_id=request_id,
						user_id=user_id,
						organisation_id=org_id,
						conversation_id=conv_id,
						tenant_id=tenant_id,
						page_url=url,
						message=req.message,
						salesforce_org_id=org_id,
						salesforce_user_id=user_id,
						salesforce_user_name=user_name,
						error=str(e),
					)
					db.add(error_log)
					db.commit()
			except Exception:
				logger.exception("Failed to log error to database for request_id=%s", request_id)

			write_jsonl(
				structured_log_path,
				{
					"event": "chat_error",
					"requestId": request_id,
					"error": str(e),
					"conversationId": req.conversationId,
					"timestamp": datetime.now().isoformat(),
				},
			)
			logger.error("Internal ZAS error request_id=%s", request_id)
			raise HTTPException(status_code=500, detail="Internal ZAS error") from e

		else:
			try:
				with SessionLocal() as db:
					upsert_entities(
						db,
						organisation_id=org_id,
						organisation_name=org_name,
						user_id=user_id,
						user_name=user_name,
						organisation_url=url,
					)
					req_log = RequestLog(
						request_id=request_id,
						user_id=user_id,
						organisation_id=org_id,
						conversation_id=conv_id,
						tenant_id=tenant_id,
						page_url=url,
						message=req.message,
						reply=reply_text,
						tokens_used=tokens_used,
						salesforce_org_id=org_id,
						salesforce_user_id=user_id,
						salesforce_user_name=user_name,
					)
					db.add(req_log)
					db.commit()
			except Exception:
				logger.exception("DB logging failed for request_id=%s", request_id)

			write_jsonl(
				structured_log_path,
				{
					"event": "chat_response",
					"requestId": request_id,
					"conversationId": conv_id,
					"tokensUsed": tokens_used,
					"replyLength": len(reply_text),
					"replyPreview": reply_text[:200],
					"timestamp": datetime.now().isoformat(),
				},
			)

		conversation_histories[conv_id] = updated_history
		return ChatResponse(reply=reply_text, conversationId=conv_id)

	@router.post("/feedback")
	async def feedback(item: FeedbackItem = Body(...)):
		record = item.model_dump()
		record["createdAt"] = item.createdAt.isoformat()
		try:
			feedback_path = feedback_log_path
			feedback_dir = os.path.dirname(feedback_path)
			if feedback_dir:
				os.makedirs(feedback_dir, exist_ok=True)
			with open(feedback_path, "a", encoding="utf-8") as f:
				f.write(json.dumps(record, ensure_ascii=False) + "\n")
		except Exception as e:
			logger.exception("Feedback logging failed")
			raise HTTPException(status_code=500, detail="Feedback logging failed") from e
		return {"status": "ok"}

	@router.post("/reset")
	async def reset_conversation(
		req: ResetRequest = Body(...),
		x_session_id: str | None = Header(None),
	):
		conv_id = req.conversationId or x_session_id
		if not conv_id:
			return {"status": "ok", "message": "No conversation id provided"}
		if conv_id in conversation_histories:
			conversation_histories.pop(conv_id, None)
		return {"status": "ok"}

	return router
