"""
LLM Service — Google Gemini 2.5 Flash Integration
Wraps Gemini API calls with structured financial context injection.
Falls back to rule-based responses when GEMINI_API_KEY is not set.

External interface (call_llm, generate_session_title) is unchanged.
Only the provider backend was swapped from Anthropic Claude to Gemini.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Load .env explicitly so GEMINI_API_KEY is available regardless of import order.
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

logger = logging.getLogger(__name__)

_MODEL = "gemini-2.5-flash"
# Gemini 2.5 Flash uses thinking tokens internally. The thinking budget
# consumes from max_output_tokens before the visible response is written,
# so we need a large enough budget to cover both thinking + answer.
_MAX_OUTPUT_TOKENS = 8192
_CONTEXT_MESSAGES = 10  # number of recent messages to include as history

SYSTEM_PROMPT_BASE = """You are Mate, the AI Financial Companion for FinMate — a personal finance management platform.

Your role is to help users understand their finances, spot patterns, and make smarter money decisions.

## Your Personality
- Warm, knowledgeable, and direct
- Like a financially-savvy friend, not a textbook
- Use plain language; avoid jargon
- Be encouraging and constructive

## Response Rules
- Always use the currency symbol shown in the FINANCIAL CONTEXT section for all amounts — never substitute a different currency symbol
- Use markdown formatting: **bold** for key numbers, bullet lists for recommendations
- Keep responses concise but complete (2-4 paragraphs max)
- Cite which data you used at the end under "Based on:"
- If data is limited, acknowledge it and suggest uploading more transactions

## CRITICAL SAFETY RULES
- NEVER provide investment advice or stock/crypto recommendations
- NEVER guarantee financial outcomes ("you will save X")
- NEVER provide tax or legal advice
- Instead say: "This is for informational purposes only. Consult a financial advisor for personalized advice."
- If asked about investing, briefly acknowledge and redirect to general budgeting/savings

## Context provided
The FINANCIAL CONTEXT section contains the user's real data. Use it to give personalized answers.
"""


def _build_system_prompt(context_text: str) -> str:
    return f"{SYSTEM_PROMPT_BASE}\n{context_text}"


def _to_gemini_history(history: List[dict]):
    """
    Convert stored chat history to google-genai Content objects.
    Maps "assistant" → "model" as required by the Gemini API.
    Gemini requires strictly alternating user/model roles starting with user.
    """
    from google.genai import types

    # Take the last N messages and normalize roles
    recent = history[-_CONTEXT_MESSAGES:]

    # Ensure history starts with a user message (Gemini requirement)
    while recent and recent[0]["role"] != "user":
        recent = recent[1:]

    # Deduplicate consecutive same-role messages (keep last of each run)
    deduplicated: List[dict] = []
    for msg in recent:
        if deduplicated and deduplicated[-1]["role"] == msg["role"]:
            deduplicated[-1] = msg  # replace with more recent same-role message
        else:
            deduplicated.append(msg)

    msgs = []
    for msg in deduplicated:
        gemini_role = "model" if msg["role"] == "assistant" else "user"
        msgs.append(
            types.Content(
                role=gemini_role,
                parts=[types.Part(text=msg["content"])],
            )
        )
    return msgs


def call_llm(
    user_message: str,
    context_text: str,
    history: List[dict],
    intent: str = "",
) -> str:
    """
    Call Google Gemini 2.5 Flash with full financial context.
    Falls back to rule-based response if GEMINI_API_KEY is not set.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        logger.info("No GEMINI_API_KEY — using rule-based fallback")
        return _rule_based_response(user_message, context_text, intent)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        chat = client.chats.create(
            model=_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=_build_system_prompt(context_text),
                max_output_tokens=_MAX_OUTPUT_TOKENS,
                temperature=0.7,
            ),
            history=_to_gemini_history(history),
        )

        response = chat.send_message(user_message)
        text = response.text
        if not text:
            logger.error("Gemini returned empty text (finish_reason=%s)", response.candidates[0].finish_reason if response.candidates else "unknown")
            return _rule_based_response(user_message, context_text, intent)
        return text.strip()

    except Exception as exc:
        logger.exception("Gemini LLM call failed: %s", exc)
        return _rule_based_response(user_message, context_text, intent)


def generate_session_title(first_message: str) -> str:
    """Generate a short, descriptive session title from the first user message."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        return _fallback_title(first_message)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # Disable thinking for title generation — we only need 3-5 words,
        # and thinking tokens would consume the entire small budget.
        response = client.models.generate_content(
            model=_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Generate a very short (3-5 words) conversation title for this financial question. "
                    "Examples: 'Health Score Analysis', 'Food Spending Review', 'Savings Recommendations', "
                    "'Budget Risk Check', 'Monthly Summary'. Return ONLY the title, no quotes, no explanation."
                ),
                max_output_tokens=50,
                temperature=0.3,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
            contents=first_message,
        )

        title = (response.text or "").strip().strip("\"'")
        return title[:100] if title else _fallback_title(first_message)

    except Exception:
        return _fallback_title(first_message)


def _fallback_title(message: str) -> str:
    """Rule-based title generation without LLM."""
    msg = message.lower()
    title_map = [
        (["health score", "score drop", "grade"], "Health Score Analysis"),
        (["save", "saving", "cut"], "Savings Recommendations"),
        (["budget", "limit", "overspent"], "Budget Review"),
        (["summary", "overview", "summarize"], "Financial Summary"),
        (["food", "swiggy", "zomato", "restaurant"], "Food Spending Review"),
        (["subscription", "recurring", "netflix", "spotify"], "Subscription Analysis"),
        (["unusual", "anomaly", "suspicious", "spike"], "Anomaly Investigation"),
        (["forecast", "projection", "end of month"], "Spending Forecast"),
        (["category", "breakdown", "spending"], "Spending Analysis"),
        (["transaction", "merchant", "purchase"], "Transaction Lookup"),
    ]
    for keywords, title in title_map:
        if any(k in msg for k in keywords):
            return title
    return "Financial Conversation"


def _rule_based_response(message: str, context_text: str, intent: str) -> str:
    """Fallback response when GEMINI_API_KEY is not configured."""
    lines = [
        "I can see your financial data, but I need a **GEMINI_API_KEY** configured to provide AI-powered insights.",
        "",
        "**To enable Mate:**",
        "1. Get a free API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)",
        "2. Add `GEMINI_API_KEY=your_key` to `backend/.env`",
        "3. Restart the backend server",
        "",
        "**In the meantime, here's what I can see from your data:**",
        "",
    ]

    if "Income:" in context_text:
        import re
        income_m = re.search(r"Income:\s+(₹[\d,\.]+)", context_text)
        expense_m = re.search(r"Expenses:\s+(₹[\d,\.]+)", context_text)
        score_m = re.search(r"HEALTH SCORE:\s+(\d+)/100", context_text)

        if income_m:
            lines.append(f"- **Income (last 30 days):** {income_m.group(1)}")
        if expense_m:
            lines.append(f"- **Expenses (last 30 days):** {expense_m.group(1)}")
        if score_m:
            lines.append(f"- **Financial Health Score:** {score_m.group(1)}/100")
    else:
        lines.append("- No transaction data found. Upload a bank statement CSV to get started.")

    lines.append("")
    lines.append("_Add your Gemini API key to unlock full AI-powered financial analysis._")

    return "\n".join(lines)
