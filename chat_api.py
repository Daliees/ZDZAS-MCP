# chat_api.py
from __future__ import annotations

import uuid
from typing import Dict, List, Optional
import traceback
import os
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents import TResponseInputItem
from zas_agent import run_zas_chat_turn

# ---------------------------------------------------------------------------
# In-memory conversatiegeschiedenis
# ---------------------------------------------------------------------------

conversation_histories: Dict[str, List[TResponseInputItem]] = {}

app = FastAPI(title="ZAS Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # in productie strakker maken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    - als er een expliciete conversationId in de body zit, gebruik die (backend integraties)
    - anders, als er een X-Session-Id header is, gebruik die (browser / extensie sessies)
    - anders, genereer een nieuwe UUID (nieuwe conversatie)
    """

    tenant_id = req.tenantId or x_zas_tenant_id
    url = req.url or x_zas_url

    # Bepaal conversation id:
    # - via expliciete conversationId uit de body (voor backend integraties)
    # - anders via X-Session-Id header (voor browser/extensie sessies)
    # - anders een nieuwe UUID
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
        # Log e intern, maar geef geen details aan de client
        print("\n=========== ZAS INTERNAL ERROR ===========")
        traceback.print_exc()
        print("==========================================\n")
        raise HTTPException(status_code=500, detail="Internal ZAS error") from e

    conversation_histories[conv_id] = updated_history

    return ChatResponse(reply=reply_text, conversationId=conv_id)


if __name__ == "__main__":
    import uvicorn
    import os

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
