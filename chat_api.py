# chat_api.py
from __future__ import annotations

import uuid
import traceback
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Literal

from fastapi import FastAPI, HTTPException, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from langchain_core.messages import BaseMessage
from zas_agent import run_zas_chat_turn

# ---------------------------------------------------------------------------
# In-memory conversatiegeschiedenis
# ---------------------------------------------------------------------------

conversation_histories: Dict[str, List[BaseMessage]] = {}

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


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversationId: Optional[str] = Field(
        None, description="Conversation id om history te bewaren"
    )
    tenantId: Optional[str] = None
    url: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    conversationId: str


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
):
    """
    Hoofd-chat endpoint voor ZAS.

    Conversation ID resolutie:
    - als er een expliciete conversationId in de body zit, gebruik die
      (bijv. backend integraties)
    - anders, als er een X-Session-Id header is, gebruik die
      (browser / extensie sessies)
    - anders, genereer een nieuwe UUID (nieuwe conversatie)
    """
    tenant_id = req.tenantId or x_zas_tenant_id
    url = req.url or x_zas_url

    # Bepaal conversation id:
    conv_id = req.conversationId or x_session_id or str(uuid.uuid4())
    history = conversation_histories.get(conv_id, [])

    try:
        reply_text, updated_history = await run_zas_chat_turn(
            message=req.message,
            history=history,
            tenant_id=tenant_id,
            url=url,
        )
    except Exception as e:
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
