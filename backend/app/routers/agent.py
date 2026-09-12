from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.agent.ollama_client import run_agent_turn

router = APIRouter(prefix="/agent", tags=["agent"])


class ChatRequest(BaseModel):
    message: str
    # Prior conversation, in Ollama message format. The frontend/Server
    # Action is responsible for holding onto this between turns — the
    # backend itself is stateless, no session storage.
    history: list[dict] = []


class ChatResponse(BaseModel):
    reply: str
    history: list[dict]


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    reply, updated_history = run_agent_turn(db, payload.history, payload.message)
    return ChatResponse(reply=reply, history=updated_history)
