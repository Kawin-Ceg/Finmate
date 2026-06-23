"""
Intent Detection Service
Classifies user queries into financial intent categories using keyword scoring.
Returns primary intent + confidence score.
"""
from __future__ import annotations
import re
from typing import Tuple

INTENT_PATTERNS: dict[str, list[str]] = {
    "financial_summary": [
        "summarize", "summary", "overview", "how am i doing", "financial situation",
        "state of my finances", "overall", "digest", "snapshot", "give me a summary",
        "tell me about my finances", "how are my finances", "finance report",
    ],
    "health_score": [
        "health score", "financial health", "why is my score", "score drop", "score low",
        "score high", "what is my score", "grade", "financial score", "improve my score",
        "why did my score", "health grade", "financial grade",
    ],
    "budget_analysis": [
        "budget", "monthly limit", "overspent", "over budget", "budget risk",
        "budget fail", "budget exceeded", "at risk budget", "which budget",
        "budget status", "budget progress", "budget warning",
    ],
    "forecast_analysis": [
        "forecast", "projection", "projected", "end of month", "will i exceed",
        "going to overspend", "month end", "projected spend", "estimated spend",
        "on track", "will i go over", "predict", "prediction",
    ],
    "spending_analysis": [
        "spending", "overspending", "where am i spending", "biggest category",
        "most expensive", "top category", "highest spending", "where does my money go",
        "spending pattern", "spending breakdown", "category breakdown", "where is my money",
        "most spent", "spending habit",
    ],
    "transaction_search": [
        "how much did i spend on", "how much have i spent on", "spend on",
        "spent on", "purchases", "show me", "transactions for", "amazon", "swiggy",
        "zomato", "uber", "flipkart", "netflix", "show transactions", "find transactions",
        "look up", "paid to", "payments to",
    ],
    "anomaly_analysis": [
        "unusual", "anomaly", "anomalies", "weird transaction", "suspicious",
        "flagged", "spike", "abnormal", "irregular", "unexpected", "strange",
        "outlier", "unusual activity", "unusual spending",
    ],
    "subscription_analysis": [
        "subscription", "recurring", "subscriptions", "annual plan",
        "membership", "monthly plan", "auto-renew", "auto renew", "regular payment",
        "recurring expense", "fixed expenses",
    ],
    "savings_recommendation": [
        "save", "saving", "savings", "cut down", "reduce spending",
        "how can i save", "save money", "save ₹", "save rs", "where can i cut",
        "reduce expenses", "spend less", "frugal", "economize", "cut costs",
        "save this month", "increase savings",
    ],
}


def detect_intent(question: str) -> Tuple[str, float]:
    """
    Returns (intent_name, confidence_0_to_1).
    Falls back to 'general_finance_question' with 0.4 confidence.
    """
    q = question.lower().strip()

    scores: dict[str, int] = {}
    for intent, keywords in INTENT_PATTERNS.items():
        score = 0
        for kw in keywords:
            if kw in q:
                # longer keyword match = higher weight
                score += len(kw.split())
        if score:
            scores[intent] = score

    if not scores:
        return "general_finance_question", 0.4

    best_intent = max(scores, key=lambda k: scores[k])
    # Normalize: max possible score ~ 5, cap at 1.0
    confidence = min(1.0, scores[best_intent] / 5.0)
    confidence = round(max(0.5, confidence), 2)

    return best_intent, confidence


def extract_merchant_from_query(question: str) -> str | None:
    """Try to extract a merchant name from a transaction search query."""
    q = question.lower()
    patterns = [
        r"(?:spend on|spent on|spend at|paid to|transactions? (?:at|for|with))\s+([a-z0-9 ]+?)(?:\s+in|\s+last|\s+this|\s*$|\?)",
        r"(?:how much (?:did i |have i )?(?:spend|spent) on)\s+([a-z0-9 ]+?)(?:\s+in|\s+last|\s+this|\s*$|\?)",
        r"(?:show|find)\s+([a-z0-9 ]+?)\s+(?:transactions?|purchases?)",
    ]
    for pat in patterns:
        m = re.search(pat, q)
        if m:
            return m.group(1).strip()
    return None


def extract_amount_from_query(question: str) -> float | None:
    """Extract a rupee amount like ₹5000 or 5000 from the query."""
    m = re.search(r"₹\s*(\d[\d,]*)", question)
    if m:
        return float(m.group(1).replace(",", ""))
    m = re.search(r"\brs\.?\s*(\d[\d,]*)\b", question.lower())
    if m:
        return float(m.group(1).replace(",", ""))
    m = re.search(r"\b(\d{3,6})\b", question)
    if m:
        return float(m.group(1))
    return None
