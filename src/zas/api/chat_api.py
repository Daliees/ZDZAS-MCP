"""Chat API for ZAS agent interactions."""

import uuid
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..core import Config


class ChatRequest(BaseModel):
    """Chat request model."""
    
    message: str = Field(..., description="User message")
    conversationId: Optional[str] = Field(
        None,
        description="Conversation ID to maintain history"
    )
    tenantId: Optional[str] = None
    url: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    
    reply: str
    conversationId: str


class FeedbackItem(BaseModel):
    """Feedback for an agent response."""
    
    conversationId: str
    sessionId: Optional[str] = None
    userMessage: Optional[str] = None
    agentReply: str
    rating: str  # "good", "neutral", "bad"
    createdAt: datetime


class ResetRequest(BaseModel):
    """Request to reset a conversation."""
    
    conversationId: Optional[str] = None


class ChatAPI:
    """FastAPI application for chat interactions."""
    
    def __init__(self, config: Config, agent_runner: callable):
        """
        Initialize the Chat API.
        
        Args:
            config: Application configuration
            agent_runner: Function to run the agent (signature: (message, history) -> reply)
        """
        self.config = config
        self.agent_runner = agent_runner
        self.conversation_histories: Dict[str, List] = {}
        
        # Create FastAPI app
        self.app = FastAPI(title="ZAS Chat API")
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self) -> None:
        """Register API routes."""
        
        @self.app.post("/chat", response_model=ChatResponse)
        async def chat(
            req: ChatRequest,
            x_zas_tenant_id: Optional[str] = Header(None),
            x_zas_url: Optional[str] = Header(None),
            x_session_id: Optional[str] = Header(None),
        ):
            """Main chat endpoint."""
            # Resolve conversation ID
            conv_id = req.conversationId or x_session_id or str(uuid.uuid4())
            
            # Get or create history
            history = self.conversation_histories.setdefault(conv_id, [])
            
            # Run agent
            try:
                reply = self.agent_runner(req.message, history)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
            
            return ChatResponse(reply=reply, conversationId=conv_id)
        
        @self.app.post("/feedback")
        async def feedback(item: FeedbackItem):
            """Log feedback for an agent response."""
            try:
                with open(self.config.feedback_log_path, "a") as f:
                    f.write(item.model_dump_json() + "\n")
                return {"ok": True}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/reset")
        async def reset(
            req: ResetRequest,
            x_session_id: Optional[str] = Header(None),
        ):
            """Reset conversation history."""
            conv_id = req.conversationId or x_session_id
            
            if not conv_id:
                raise HTTPException(
                    status_code=400,
                    detail="Provide conversationId in body or X-Session-Id header"
                )
            
            if conv_id in self.conversation_histories:
                del self.conversation_histories[conv_id]
            
            return {"ok": True, "conversationId": conv_id}
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            return {"status": "healthy"}
