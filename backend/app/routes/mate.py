"""
Mate — AI Financial Companion Routes
Complete chat, session management, search, export, and suggestions.
"""
from __future__ import annotations

import io
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies import get_current_user
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.mate import (
    ChatRequest,
    ChatResponse,
    ExportRequest,
    SearchResult,
    SessionDetail,
    SessionSummary,
    SessionUpdate,
    SuggestionItem,
)
from app.services.context_builder import build_context, context_to_prompt_text
from app.services.financial_reasoning_service import (
    analyze_budget_risk,
    analyze_savings_opportunity,
    analyze_spending,
    explain_health_score,
    get_used_services,
    search_transactions_by_merchant,
)
from app.services.intent_service import (
    detect_intent,
    extract_amount_from_query,
    extract_merchant_from_query,
)
from app.services.llm_service import call_llm, generate_session_title

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mate", tags=["Mate"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get_session_or_404(session_id: int, user_id: int, db: Session) -> ChatSession:
    s = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id,
    ).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return s


def _session_summary(s: ChatSession) -> SessionSummary:
    msgs = s.messages
    last_preview = None
    if msgs:
        last_user = next((m for m in reversed(msgs) if m.role == "assistant"), None)
        if last_user:
            last_preview = last_user.content[:120].strip()
    return SessionSummary(
        id=s.id,
        title=s.title,
        created_at=s.created_at,
        updated_at=s.updated_at,
        last_message_at=s.last_message_at,
        last_message_preview=last_preview,
        message_count=len(msgs),
    )


def _build_enriched_user_message(question: str, intent: str, ctx: dict, db: Session, user_id: int) -> str:
    """Prepend structured reasoning data to the user question for the LLM."""
    extra = []

    if intent == "savings_recommendation":
        target = extract_amount_from_query(question)
        reasoning = analyze_savings_opportunity(ctx, target)
        if reasoning["possible"]:
            extra.append(f"[REASONING] Savings analysis: potential ₹{reasoning['potential_savings']:,.2f}/month identified.")
            extra.append(f"High-spend categories: {', '.join(c['category'] for c in reasoning['high_spend_categories'])}")
            if reasoning["recommendations"]:
                extra.append("Pre-computed recommendations: " + " | ".join(reasoning["recommendations"]))

    elif intent in ("budget_analysis", "forecast_analysis"):
        budget_risk = analyze_budget_risk(ctx)
        if budget_risk["has_budgets"]:
            most_at_risk = budget_risk["most_at_risk"]
            if most_at_risk:
                extra.append(f"[REASONING] Most at-risk budget: {most_at_risk['category']} ({most_at_risk['risk']}, {most_at_risk['pct_used']:.0f}% used)")
            extra.append(f"Exceeded: {budget_risk['exceeded_count']} | High risk: {budget_risk['high_risk_count']} | Safe: {budget_risk['safe_count']}")

    elif intent == "health_score":
        hs = explain_health_score(ctx)
        weak = hs["weakest_factor"]
        extra.append(f"[REASONING] Weakest factor: {weak['factor']} ({weak['score']}/{weak['max']} pts, {weak['pct']}%)")
        if hs["improvement_tips"]:
            extra.append("Improvement tips: " + " | ".join(hs["improvement_tips"]))

    elif intent == "spending_analysis":
        sp = analyze_spending(ctx)
        if sp["has_data"]:
            extra.append(f"[REASONING] Total expense: {sp['total_expense_fmt']}, discretionary: {sp['discretionary_total_fmt']} ({sp['discretionary_pct']}%)")

    elif intent == "transaction_search":
        merchant = extract_merchant_from_query(question)
        if merchant:
            results = search_transactions_by_merchant(
                user_id, db, merchant, ctx.get("currency_symbol", "₹")
            )
            extra.append(f"[TRANSACTION SEARCH] '{merchant}': {results['found']} transactions, total {results['total_fmt']}")
            if results["transactions"]:
                for t in results["transactions"][:5]:
                    extra.append(f"  • {t['date']} — {t['merchant']}: {t['amount_fmt']} ({t['category']})")

    if extra:
        return "[PRE-ANALYZED DATA]\n" + "\n".join(extra) + "\n\n[USER QUESTION]\n" + question
    return question


# ---------------------------------------------------------------------------
# POST /mate/chat
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # --- Get or create session ---
    if req.session_id:
        session = _get_session_or_404(req.session_id, current_user.id, db)
        is_new_session = False
    else:
        session = ChatSession(user_id=current_user.id, title="New Conversation")
        db.add(session)
        db.flush()
        is_new_session = True

    # --- Detect intent ---
    intent, intent_confidence = detect_intent(message)

    # --- Build financial context ---
    ctx = build_context(current_user.id, db, intent=intent)
    context_text = context_to_prompt_text(ctx)

    # --- Build enriched message with pre-analyzed reasoning ---
    enriched_message = _build_enriched_user_message(message, intent, ctx, db, current_user.id)

    # --- Get recent history for context window ---
    history_msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in reversed(history_msgs)]

    # --- Call LLM ---
    answer = call_llm(
        user_message=enriched_message,
        context_text=context_text,
        history=history,
        intent=intent,
    )

    # --- Determine sources and services ---
    used_services = get_used_services(intent)
    sources = _intent_to_sources(intent, ctx)
    confidence = f"{int(intent_confidence * 100)}%"

    # --- Persist user message ---
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=message,
        intent=intent,
        created_at=_now_utc(),
    )
    db.add(user_msg)

    # --- Persist assistant message ---
    asst_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=answer,
        sources=sources,
        confidence=confidence,
        used_services=used_services,
        intent=intent,
        created_at=_now_utc(),
    )
    db.add(asst_msg)

    # --- Auto-generate title for new sessions ---
    if is_new_session:
        session.title = generate_session_title(message)

    # --- Update session timestamps ---
    session.last_message_at = _now_utc()
    session.updated_at = _now_utc()

    # --- Rolling summary: summarize old messages if chat is long ---
    total_messages = len(history_msgs) + 2  # +2 for the new ones
    if total_messages > 30 and total_messages % 10 == 0:
        _update_session_summary(session, history, db)

    db.commit()
    db.refresh(asst_msg)

    return ChatResponse(
        session_id=session.id,
        session_title=session.title,
        answer=answer,
        confidence=confidence,
        used_services=used_services,
        sources=sources,
        intent=intent,
        message_id=asst_msg.id,
    )


def _intent_to_sources(intent: str, ctx: dict) -> List[str]:
    SOURCE_MAP = {
        "financial_summary": ["Analytics Engine", "Budget Forecasting", "Health Score", "Anomaly Detection"],
        "health_score": ["Health Score Engine", "Transaction Analytics"],
        "budget_analysis": ["Budget Service", "Forecast Algorithm"],
        "forecast_analysis": ["Budget Forecasting", "Daily Rate Projection"],
        "spending_analysis": ["Transaction Analytics", "Category Breakdown"],
        "transaction_search": ["Transaction History"],
        "anomaly_analysis": ["Anomaly Detection Engine"],
        "subscription_analysis": ["Anomaly Detection (Subscription Pattern)"],
        "savings_recommendation": ["Analytics Engine", "Budget Forecasting", "Transaction History"],
        "general_finance_question": ["Analytics Engine"],
    }
    sources = SOURCE_MAP.get(intent, ["Analytics Engine"])
    if ctx.get("has_data"):
        sources.append(f"Transaction History ({ctx.get('total_transactions', 0)} records)")
    return sources


def _update_session_summary(session: ChatSession, history: list, db: Session):
    """Generate a brief rolling summary of older messages (stored, not sent to LLM every time)."""
    try:
        recent_user_msgs = [h["content"] for h in history if h["role"] == "user"][-5:]
        summary = f"Previously discussed: {'; '.join(recent_user_msgs[:3])}"
        session.session_summary = summary[:500]
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------

@router.post("/sessions", response_model=SessionSummary)
def create_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = ChatSession(user_id=current_user.id, title="New Conversation")
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_summary(session)


@router.get("/sessions", response_model=List[SessionSummary])
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.last_message_at.desc())
        .all()
    )
    return [_session_summary(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_session_or_404(session_id, current_user.id, db)
    return SessionDetail(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        last_message_at=session.last_message_at,
        messages=[
            {
                "id": m.id,
                "session_id": m.session_id,
                "role": m.role,
                "content": m.content,
                "sources": m.sources,
                "confidence": m.confidence,
                "used_services": m.used_services,
                "intent": m.intent,
                "created_at": m.created_at,
            }
            for m in session.messages
        ],
    )


@router.put("/sessions/{session_id}", response_model=SessionSummary)
def rename_session(
    session_id: int,
    body: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_session_or_404(session_id, current_user.id, db)
    session.title = body.title[:200].strip()
    session.updated_at = _now_utc()
    db.commit()
    db.refresh(session)
    return _session_summary(session)


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_session_or_404(session_id, current_user.id, db)
    db.delete(session)
    db.commit()
    return {"detail": "Session deleted"}


@router.delete("/sessions")
def delete_all_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(ChatSession).filter(ChatSession.user_id == current_user.id).delete()
    db.commit()
    return {"detail": "All sessions deleted"}


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@router.get("/search", response_model=List[SearchResult])
def search_chats(
    q: str = Query(..., min_length=2),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q_lower = f"%{q.lower()}%"
    rows = (
        db.query(ChatMessage, ChatSession.title)
        .join(ChatSession, ChatSession.id == ChatMessage.session_id)
        .filter(
            ChatSession.user_id == current_user.id,
            ChatMessage.content.ilike(q_lower),
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
        .all()
    )

    results = []
    for m, session_title in rows:
        preview = m.content[:150].strip().replace("\n", " ")
        results.append(
            SearchResult(
                session_id=m.session_id,
                session_title=session_title or "Unknown",
                message_id=m.id,
                role=m.role,
                content_preview=preview,
                created_at=m.created_at,
            )
        )
    return results


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@router.post("/export")
def export_chats(
    req: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.session_id:
        sessions = [_get_session_or_404(req.session_id, current_user.id, db)]
    else:
        sessions = (
            db.query(ChatSession)
            .filter(ChatSession.user_id == current_user.id)
            .order_by(ChatSession.last_message_at.desc())
            .all()
        )

    if req.format == "json":
        data = []
        for s in sessions:
            data.append({
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at.isoformat(),
                "messages": [
                    {
                        "role": m.role,
                        "content": m.content,
                        "created_at": m.created_at.isoformat(),
                        "used_services": m.used_services,
                    }
                    for m in s.messages
                ],
            })
        content = json.dumps(data, indent=2, ensure_ascii=False)
        media_type = "application/json"
        filename = "mate_conversations.json"

    else:  # markdown
        lines = ["# Mate — FinMate AI Companion Conversations\n"]
        for s in sessions:
            lines.append(f"## {s.title}")
            lines.append(f"_Created: {s.created_at.strftime('%d %b %Y %H:%M')}_\n")
            for m in s.messages:
                prefix = "**You:**" if m.role == "user" else "**Mate:**"
                lines.append(f"{prefix} {m.content}\n")
            lines.append("---\n")
        content = "\n".join(lines)
        media_type = "text/markdown"
        filename = "mate_conversations.md"

    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ---------------------------------------------------------------------------
# Suggestions
# ---------------------------------------------------------------------------

@router.get("/suggestions", response_model=List[SuggestionItem])
def get_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ctx = build_context(current_user.id, db)

    suggestions = [
        SuggestionItem(text="Give me a summary of my finances", intent="financial_summary", icon="BarChart2"),
        SuggestionItem(text="Why did my health score drop?", intent="health_score", icon="Heart"),
        SuggestionItem(text="Which budget is most at risk?", intent="budget_analysis", icon="AlertTriangle"),
        SuggestionItem(text="Where am I overspending?", intent="spending_analysis", icon="TrendingUp"),
        SuggestionItem(text="Show unusual transactions this month", intent="anomaly_analysis", icon="Zap"),
        SuggestionItem(text="Can I save ₹5000 this month?", intent="savings_recommendation", icon="PiggyBank"),
        SuggestionItem(text="What are my recurring subscriptions?", intent="subscription_analysis", icon="RefreshCw"),
        SuggestionItem(text="How much did I spend on food last month?", intent="transaction_search", icon="ShoppingCart"),
    ]

    # Personalize based on context
    if ctx.get("has_data"):
        cats = ctx.get("categories", [])
        budgets = ctx.get("budgets", [])
        anomalies = ctx.get("anomalies", [])

        if cats:
            top_cat = cats[0]["category"]
            suggestions.insert(1, SuggestionItem(
                text=f"Why is {top_cat} my biggest expense?",
                intent="spending_analysis",
                icon="TrendingUp",
            ))

        at_risk = [b for b in budgets if b.get("risk") in ("high", "exceeded")]
        if at_risk:
            suggestions.insert(2, SuggestionItem(
                text=f"My {at_risk[0]['category']} budget is at risk. What should I do?",
                intent="budget_analysis",
                icon="AlertTriangle",
            ))

        if anomalies:
            suggestions.insert(3, SuggestionItem(
                text=f"Explain this anomaly: {anomalies[0]['title']}",
                intent="anomaly_analysis",
                icon="Zap",
            ))

    return suggestions[:8]
