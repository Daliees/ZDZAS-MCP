# chat_api.py
from __future__ import annotations

import uuid
import traceback
import os
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents import TResponseInputItem
from zas_agent import run_zas_chat_turn
from db import SessionLocal, RequestLog, init_db, upsert_entities

# Load .env file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)
# Logging setup (file + structured JSONL)
# ---------------------------------------------------------------------------
LOG_DIR = Path(BASE_DIR) / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "chat_api.log"
STRUCTURED_LOG_PATH = os.getenv("ZAS_CHAT_JSONL", str(LOG_DIR / "chat_events.jsonl"))
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    _fh = RotatingFileHandler(str(LOG_FILE), maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
    _fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(_fh)

def _write_jsonl(path: str, obj: dict) -> None:
    """Append a structured log record as JSONL. Fail-safe (logs exception)."""
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception:
        logger.exception("Failed to write structured log record")
init_db()

# ---------------------------------------------------------------------------
# In-memory conversatiegeschiedenis
# ---------------------------------------------------------------------------

conversation_histories: Dict[str, List[TResponseInputItem]] = {}

# Pad voor feedback-log (JSON Lines)
FEEDBACK_LOG_PATH = os.getenv("ZAS_FEEDBACK_LOG", "zas_feedback_log.jsonl")

# ---------------------------------------------------------------------------
# FastAPI app + CORS
# ---------------------------------------------------------------------------

app = FastAPI(title="ZAS Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # voor productie strakker maken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic modellen
# ---------------------------------------------------------------------------

class SalesforceContext(BaseModel):
    """Salesforce context information"""
    orgId: Optional[str] = None
    userId: Optional[str] = None
    userName: Optional[str] = None
    userEmail: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversationId: Optional[str] = Field(
        None, description="Conversation id om history te bewaren"
    )
    tenantId: Optional[str] = None
    url: Optional[str] = None
    salesforceContext: Optional[SalesforceContext] = None


class ChatResponse(BaseModel):
    reply: str
    conversationId: str


def estimate_tokens(message: str, reply: str) -> int:
    """Rough token estimate to log usage without model introspection."""
    return max(1, int((len(message) + len(reply)) / 4))


class FeedbackItem(BaseModel):
    """
    Feedback van de extensie voor een specifiek agent-antwoord.
    Wordt als JSONL gelogd zodat je het later makkelijk kunt analyseren.
    """

    conversationId: str
    sessionId: Optional[str] = None
    userMessage: Optional[str] = None
    agentReply: str
    rating: Literal["good", "neutral", "bad"]
    createdAt: datetime


class ResetRequest(BaseModel):
    """
    Request voor het resetten van een conversatie.
    Als conversationId None is, wordt de X-Session-Id header gebruikt.
    """

    conversationId: Optional[str] = None


# ---------------------------------------------------------------------------
# /chat endpoint
# ---------------------------------------------------------------------------


@app.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    x_zas_tenant_id: Optional[str] = Header(None),
    x_zas_url: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None),
    x_salesforce_org_id: Optional[str] = Header(None, alias="X-Salesforce-Org-Id"),
    x_salesforce_user_id: Optional[str] = Header(None, alias="X-Salesforce-User-Id"),
):
    """
    Hoofd-chat endpoint voor ZAS.

    Conversation ID resolutie:
    - als er een expliciete conversationId in de body zit, gebruik die (bijv. backend integraties)
    - anders, als er een X-Session-Id header is, gebruik die (browser / extensie sessies)
    - anders, genereer een nieuwe UUID (nieuwe conversatie)
    """

    request_id = str(uuid.uuid4())
    
    # ========== VERBOSE LOGGING START ==========
    print("\n" + "="*80)
    print("📥 INCOMING CHAT REQUEST")
    print("="*80)
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print(f"🔖 Request ID: {request_id}")
    logger.info(f"Incoming /chat request request_id={request_id}")
    print(f"\n📨 Request Body:")
    print(f"  • message: {req.message!r}")
    print(f"  • conversationId: {req.conversationId!r}")
    print(f"  • tenantId: {req.tenantId!r}")
    print(f"  • url: {req.url!r}")
    
    # Log Salesforce context if present
    if req.salesforceContext:
        print(f"\n🏢 Salesforce Context (from body):")
        print(f"  • Org ID: {req.salesforceContext.orgId!r}")
        print(f"  • User ID: {req.salesforceContext.userId!r}")
        print(f"  • User Name: {req.salesforceContext.userName!r}")
        print(f"  • User Email: {req.salesforceContext.userEmail!r}")
    
    print(f"\n📋 Headers:")
    print(f"  • X-Zas-Tenant-Id: {x_zas_tenant_id!r}")
    print(f"  • X-Zas-Url: {x_zas_url!r}")
    print(f"  • X-Session-Id: {x_session_id!r}")
    print(f"  • X-Salesforce-Org-Id: {x_salesforce_org_id!r}")
    print(f"  • X-Salesforce-User-Id: {x_salesforce_user_id!r}")
    
    print(f"\n🔍 Computed Values:")
    
    tenant_id = req.tenantId or x_zas_tenant_id
    url = req.url or x_zas_url
    conv_id = req.conversationId or x_session_id or str(uuid.uuid4())
    org_id = (req.salesforceContext.orgId if req.salesforceContext else None) or x_salesforce_org_id
    user_id = (req.salesforceContext.userId if req.salesforceContext else None) or x_salesforce_user_id
    user_name = req.salesforceContext.userName if req.salesforceContext else None
    org_name = None
    
    print(f"  • Final tenant_id: {tenant_id!r}")
    print(f"  • Final url: {url!r}")
    print(f"  • Final conv_id: {conv_id!r}")
    
    history = conversation_histories.get(conv_id, [])
    print(f"\n📚 Conversation History:")
    print(f"  • History length: {len(history)} messages")
    print("="*80 + "\n")
    # ========== VERBOSE LOGGING END ==========
    
    # Structured request log
    _write_jsonl(STRUCTURED_LOG_PATH, {
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
    })

    try:
        reply_text, updated_history = await run_zas_chat_turn(
            message=req.message,
            history=history,
            tenant_id=tenant_id,
            url=url,
        )
        
        # ========== VERBOSE RESPONSE LOGGING ==========
        print("\n" + "="*80)
        print("📤 OUTGOING CHAT RESPONSE")
        print("="*80)
        print(f"  • Reply length: {len(reply_text)} characters")
        print(f"  • Reply preview: {reply_text[:100]}...")
        print(f"  • Updated history length: {len(updated_history)} messages")
        print(f"  • Conversation ID: {conv_id!r}")
        print("="*80 + "\n")
        # ========== VERBOSE RESPONSE LOGGING END ==========

        # ========== REQUEST LOGGING TO DB ==========
        try:
            tokens_used = estimate_tokens(req.message, reply_text)
            with SessionLocal() as db:
                upsert_entities(db, organisation_id=org_id, organisation_name=org_name, user_id=user_id, user_name=user_name)
                req_log = RequestLog(
                    request_id=request_id,
                    user_id=user_id,
                    organisation_id=org_id,
                    conversation_id=conv_id,
                    tenant_id=tenant_id,
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
            print("\n=========== ZAS DB LOGGING ERROR ===========")
            traceback.print_exc()
            print("============================================\n")
        
        # Structured response log
        _write_jsonl(STRUCTURED_LOG_PATH, {
            "event": "chat_response",
            "requestId": request_id,
            "conversationId": conv_id,
            "tokensUsed": tokens_used,
            "replyLength": len(reply_text),
            "replyPreview": reply_text[:200],
            "timestamp": datetime.now().isoformat(),
        })
        
    except Exception as e:
        logger.exception("Unhandled error on /chat request_id=%s", request_id)
        
        # Log error to database
        try:
            with SessionLocal() as db:
                upsert_entities(db, organisation_id=org_id, organisation_name=org_name, user_id=user_id, user_name=user_name)
                error_log = RequestLog(
                    request_id=request_id,
                    user_id=user_id,
                    organisation_id=org_id,
                    conversation_id=conv_id,
                    tenant_id=tenant_id,
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
        
        _write_jsonl(STRUCTURED_LOG_PATH, {
            "event": "chat_error",
            "requestId": request_id,
            "error": str(e),
            "conversationId": req.conversationId,
            "timestamp": datetime.now().isoformat(),
        })
        # Log intern, maar geef geen stacktrace aan de client
        print("\n=========== ZAS INTERNAL ERROR ===========")
        traceback.print_exc()
        print("==========================================\n")
        raise HTTPException(status_code=500, detail="Internal ZAS error") from e

    conversation_histories[conv_id] = updated_history

    return ChatResponse(reply=reply_text, conversationId=conv_id)


# ---------------------------------------------------------------------------
# /feedback endpoint
# ---------------------------------------------------------------------------


@app.post("/feedback")
async def feedback(item: FeedbackItem = Body(...)):
    """
    Slaat feedback van de extensie op in een JSONL-bestand.
    Elke regel in FEEDBACK_LOG_PATH is één JSON-object.

    Dit bestand kun je later uitlezen met Python, Excel, BI, etc.
    """
    record = item.model_dump()
    # Datums altijd in ISO-formaat loggen voor makkelijke parsing
    record["createdAt"] = item.createdAt.isoformat()

    try:
        # Zorg dat directory bestaat (als er een pad is opgegeven)
        feedback_dir = os.path.dirname(FEEDBACK_LOG_PATH)
        if feedback_dir:
            os.makedirs(feedback_dir, exist_ok=True)

        with open(FEEDBACK_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        print("\n=========== ZAS FEEDBACK LOG ERROR ===========")
        traceback.print_exc()
        print("==============================================\n")
        raise HTTPException(status_code=500, detail="Feedback logging failed") from e

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# /reset endpoint
# ---------------------------------------------------------------------------


@app.post("/reset")
async def reset_conversation(
    req: ResetRequest = Body(...),
    x_session_id: Optional[str] = Header(None),
):
    """
    Reset de conversatiegeschiedenis voor een conversationId of sessionId.

    Werkt zo samen met de extensie:
    - De extensie stuurt óf een expliciete conversationId in de body
    - Óf alleen de X-Session-Id header
    We pakken wat beschikbaar is en verwijderen die key uit conversation_histories.
    """
    conv_id = req.conversationId or x_session_id
    if not conv_id:
        # Geen id doorgegeven -> er is niets te wissen; is geen fout.
        return {"status": "ok", "message": "No conversation id provided"}

    if conv_id in conversation_histories:
        conversation_histories.pop(conv_id, None)

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Entrypoint (standalone draaien)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("ZAS_CHAT_PORT", "9000"))

    # 0.0.0.0 = luister op alle netwerkinterfaces
    # - lokaal:     http://127.0.0.1:9000/chat
    # - LAN:        http://<lan-ip>:9000/chat
    # - via ngrok:  https://...ngrok-free.app/chat
    uvicorn.run(
        "chat_api:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
