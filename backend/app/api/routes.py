from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.services.agent import run_agent

logger = logging.getLogger(__name__)
router = APIRouter()


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[Message]] = []


class ChatResponse(BaseModel):
    response: str
    status: str = "success"


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint. Accepts a user message and chat history, returns agent response."""
    try:
        history = [{"role": m.role, "content": m.content} for m in (request.chat_history or [])]
        response = run_agent(request.message, history)
        return ChatResponse(response=response, status="success")
    except Exception as e:
        logger.exception("Chat endpoint error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "TailorTalk API"}
