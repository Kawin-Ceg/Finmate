from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None


class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    sources: Optional[List[str]] = None
    confidence: Optional[str] = None
    used_services: Optional[List[str]] = None
    intent: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    session_id: int
    session_title: str
    answer: str
    confidence: str
    used_services: List[str]
    sources: List[str]
    intent: str
    message_id: int


class SessionSummary(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime
    last_message_preview: Optional[str] = None
    message_count: int = 0

    model_config = {"from_attributes": True}


class SessionDetail(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime
    messages: List[MessageResponse]

    model_config = {"from_attributes": True}


class SessionUpdate(BaseModel):
    title: str


class SearchResult(BaseModel):
    session_id: int
    session_title: str
    message_id: int
    role: str
    content_preview: str
    created_at: datetime


class SuggestionItem(BaseModel):
    text: str
    intent: str
    icon: str


class ExportRequest(BaseModel):
    format: str = "markdown"  # markdown | json
    session_id: Optional[int] = None  # None = all sessions
