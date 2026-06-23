"""
RAG Evaluation — Mate Financial Assistant
==========================================
20-question evaluation using an LLM-as-judge (Gemini) to score answers on:
  - Relevance    (1-5): Does the answer directly address the question?
  - Groundedness (1-5): Is every claim supported by the provided context?
  - Helpfulness  (1-5): Would a real user find this actionable and clear?

Approach: RAGAS-inspired single-model judge. No DB required — uses a
synthetic but realistic Indian user context injected directly into the
LLM pipeline, bypassing the database layer entirely.

Usage:
  cd backend
  python scripts/evaluate_rag.py
"""
from __future__ import annotations

import json
import os
import sys
import textwrap
import time
from pathlib import Path

# ── path setup ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env", override=True)

from app.services.context_builder import context_to_prompt_text
from app.services.llm_service import call_llm

# ── Synthetic user context (matches build_context() output schema) ──────────

SYNTHETIC_CTX = {
    "has_data": True,
    "data_window": "last 30 days",
    "today": "June 20, 2026",
    "currency_symbol": "₹",
    "overview": {
        "income": 85000,
        "expense": 62400,
        "savings": 22600,
        "savings_rate": 26.6,
        "income_fmt": "₹85,000.00",
        "expense_fmt": "₹62,400.00",
        "savings_fmt": "₹22,600.00",
    },
    "health": {
        "score": 72,
        "grade": "B",
        "status": "Good",
        "insights": [
            "Savings rate of 26.6% is above the recommended 20% — keep it up.",
            "Food spending is 29.6% of total expenses — above the 20% guideline.",
            "3 active budgets. Food budget exceeded by ₹3,500 this month.",
            "2 subscriptions detected (₹1,067/mo). Review if all are used.",
        ],
        "breakdown": {
            "savings_rate": 25, "savings_rate_max": 35,
            "expense_stability": 18, "expense_stability_max": 25,
            "income_consistency": 20, "income_consistency_max": 25,
            "diversification": 9,  "diversification_max": 15,
        },
    },
    "categories": [
        {"category": "Food",          "amount": 18500, "percentage": 29.6},
        {"category": "Transport",     "amount": 9200,  "percentage": 14.7},
        {"category": "Shopping",      "amount": 8800,  "percentage": 14.1},
        {"category": "Entertainment", "amount": 6400,  "percentage": 10.3},
        {"category": "Utilities",     "amount": 5200,  "percentage": 8.3},
        {"category": "Health",        "amount": 4800,  "percentage": 7.7},
        {"category": "Subscriptions", "amount": 1067,  "percentage": 1.7},
        {"category": "Other",         "amount": 8433,  "percentage": 13.5},
    ],
    "top_merchants": [
        {"merchant": "Swiggy",        "total_amount": 8200},
        {"merchant": "Amazon",        "total_amount": 6400},
        {"merchant": "Ola",           "total_amount": 4800},
        {"merchant": "Apollo Pharmacy","total_amount": 3600},
        {"merchant": "Netflix",       "total_amount": 649},
    ],
    "budgets": [
        {
            "category": "Food",     "monthly_limit": 15000, "current_spend": 18500,
            "pct_used": 123.3, "risk": "exceeded",
            "forecast": {"projected_spend": 18500, "exceed_probability": 0.97,
                         "lower_bound": 17200, "upper_bound": 19800,
                         "forecast_method": "historical_prior",
                         "explanation": "Food spending exceeds budget by ₹3,500 this month."},
        },
        {
            "category": "Shopping", "monthly_limit": 10000, "current_spend": 8800,
            "pct_used": 88.0, "risk": "high",
            "forecast": {"projected_spend": 10400, "exceed_probability": 0.62,
                         "lower_bound": 9200, "upper_bound": 11600,
                         "forecast_method": "blended",
                         "explanation": "At current pace, Shopping will exceed budget by ~₹400."},
        },
        {
            "category": "Transport","monthly_limit": 12000, "current_spend": 9200,
            "pct_used": 76.7, "risk": "watch",
            "forecast": {"projected_spend": 11040, "exceed_probability": 0.18,
                         "lower_bound": 9800, "upper_bound": 12280,
                         "forecast_method": "linear_daily_rate",
                         "explanation": "Transport on track; 18% chance of exceeding ₹12,000."},
        },
    ],
    "recent_transactions": [
        {"date": "20 Jun 2026", "merchant": "Swiggy",         "amount": 420,  "amount_fmt": "₹420.00",  "category": "Food"},
        {"date": "19 Jun 2026", "merchant": "Amazon",         "amount": 6400, "amount_fmt": "₹6,400.00","category": "Shopping"},
        {"date": "18 Jun 2026", "merchant": "Ola",            "amount": 380,  "amount_fmt": "₹380.00",  "category": "Transport"},
        {"date": "17 Jun 2026", "merchant": "Netflix",        "amount": 649,  "amount_fmt": "₹649.00",  "category": "Subscriptions"},
        {"date": "16 Jun 2026", "merchant": "Apollo Pharmacy","amount": 1200, "amount_fmt": "₹1,200.00","category": "Health"},
        {"date": "15 Jun 2026", "merchant": "Swiggy",         "amount": 980,  "amount_fmt": "₹980.00",  "category": "Food"},
        {"date": "14 Jun 2026", "merchant": "Spotify",        "amount": 119,  "amount_fmt": "₹119.00",  "category": "Subscriptions"},
        {"date": "13 Jun 2026", "merchant": "Big Bazaar",     "amount": 2200, "amount_fmt": "₹2,200.00","category": "Shopping"},
    ],
    "anomalies": [
        {
            "type": "large_transaction", "severity": "high",
            "title": "Unusually large Amazon purchase",
            "description": "₹6,400 on Amazon on Jun 19 — 2.4× your usual Shopping transaction.",
            "score": 0.87,
        },
        {
            "type": "spending_spike", "severity": "medium",
            "title": "Entertainment spike in June",
            "description": "₹6,400 in Entertainment this month, 58% above your 3-month average of ₹4,050.",
            "score": 0.71,
        },
        {
            "type": "subscription", "severity": "low",
            "title": "Subscription: Netflix",
            "description": "Recurring ₹649/mo detected via consistent monthly charge.",
            "score": 0.60,
        },
        {
            "type": "subscription", "severity": "low",
            "title": "Subscription: Spotify",
            "description": "Recurring ₹119/mo detected.",
            "score": 0.55,
        },
    ],
    "subscriptions": [
        {"merchant": "Netflix", "amount": 649},
        {"merchant": "Spotify", "amount": 119},
        {"merchant": "Amazon Prime", "amount": 299},
    ],
    "monthly_trend": [
        {"month": "Mar 2026", "spending": 58200},
        {"month": "Apr 2026", "spending": 61800},
        {"month": "May 2026", "spending": 59500},
        {"month": "Jun 2026", "spending": 62400},
    ],
    "total_transactions": 187,
    "total_budgets": 3,
    "total_anomalies": 4,
}

# ── 20 test questions ────────────────────────────────────────────────────────

TEST_CASES = [
    # 1 per intent — 10 questions, 20 API calls total (fits 20 RPD free tier)
    {
        "id": 1, "intent": "financial_summary",
        "question": "Give me a complete summary of my finances this month.",
        "key_points": ["income", "expense", "savings", "health score", "budget"],
    },
    {
        "id": 2, "intent": "health_score",
        "question": "Why is my health score 72 and not higher?",
        "key_points": ["savings rate", "expense stability", "food", "budget exceeded"],
    },
    {
        "id": 3, "intent": "budget_analysis",
        "question": "Which of my budgets is most at risk right now?",
        "key_points": ["Food", "exceeded", "3,500", "123"],
    },
    {
        "id": 4, "intent": "budget_analysis",
        "question": "Will I exceed my Shopping budget this month?",
        "key_points": ["Shopping", "10,000", "8,800", "62%", "10,400"],
    },
    {
        "id": 5, "intent": "spending_analysis",
        "question": "Where am I spending the most money?",
        "key_points": ["Food", "18,500", "29", "Transport", "Shopping"],
    },
    {
        "id": 6, "intent": "spending_analysis",
        "question": "How has my spending changed over the last few months?",
        "key_points": ["March", "April", "May", "June", "trend"],
    },
    {
        "id": 7, "intent": "savings_recommendation",
        "question": "How can I save more money this month?",
        "key_points": ["food", "Swiggy", "subscriptions", "Entertainment", "budget"],
    },
    {
        "id": 8, "intent": "transaction_search",
        "question": "How much have I spent on Swiggy recently?",
        "key_points": ["Swiggy", "8,200", "Food"],
    },
    {
        "id": 9, "intent": "anomaly_analysis",
        "question": "Are there any unusual transactions I should know about?",
        "key_points": ["Amazon", "6,400", "2.4x", "Entertainment", "spike"],
    },
    {
        "id": 10, "intent": "subscription_analysis",
        "question": "What subscriptions am I paying for?",
        "key_points": ["Netflix", "649", "Spotify", "119", "Amazon Prime", "299"],
    },
]

# ── LLM judge ────────────────────────────────────────────────────────────────

JUDGE_SYSTEM = textwrap.dedent("""
    You are an impartial evaluator for a RAG (Retrieval-Augmented Generation)
    financial assistant. Your job is to score AI responses using ONLY the
    provided financial context — never your own knowledge.

    Score each answer on THREE criteria (integer 1-5 each):

    1. RELEVANCE (1-5):
       5 = Directly and completely addresses the question
       4 = Addresses question with minor omissions
       3 = Partially addresses the question
       2 = Tangentially related but misses the main point
       1 = Off-topic or irrelevant

    2. GROUNDEDNESS (1-5):
       5 = Every claim is directly supported by the provided context
       4 = Mostly grounded; minor reasonable inferences
       3 = Mix of grounded and ungrounded claims
       2 = Several claims not supported by context
       1 = Hallucinated or contradicts the context

    3. HELPFULNESS (1-5):
       5 = Highly actionable; clear, specific recommendations
       4 = Helpful with some vague parts
       3 = Somewhat helpful
       2 = Minimal actionable value
       1 = Not helpful

    Respond with ONLY valid JSON in this exact format — no explanation, no markdown:
    {"relevance": <int>, "groundedness": <int>, "helpfulness": <int>, "reason": "<one sentence>"}
""").strip()


def _call_with_backoff(fn, *args, max_retries=5, **kwargs):
    """Call fn(*args, **kwargs) with exponential backoff on 429 errors."""
    import re
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                # Parse suggested retry delay from error message
                m = re.search(r"retry in (\d+)", msg)
                wait = int(m.group(1)) + 3 if m else 30 * (2 ** attempt)
                print(f"  [rate limit] waiting {wait}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Max retries exceeded after {max_retries} attempts")


def _judge_answer(question: str, context_text: str, answer: str, api_key: str) -> dict:
    """Call Gemini to score one Q/A pair. Returns {relevance, groundedness, helpfulness}."""
    from google import genai
    from google.genai import types

    prompt = textwrap.dedent(f"""
        === FINANCIAL CONTEXT PROVIDED TO THE ASSISTANT ===
        {context_text}

        === USER QUESTION ===
        {question}

        === ASSISTANT ANSWER ===
        {answer}

        === YOUR TASK ===
        Score the answer using ONLY the context above. Return JSON only.
    """).strip()

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=JUDGE_SYSTEM,
            max_output_tokens=256,
            temperature=0.1,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
        contents=prompt,
    )
    text = (response.text or "").strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


# ── Main evaluation loop ─────────────────────────────────────────────────────

def run_evaluation():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set in .env — cannot run evaluation.")
        sys.exit(1)

    context_text = context_to_prompt_text(SYNTHETIC_CTX)
    print(f"\n{'='*60}")
    print("  FinMate RAG Evaluation — Mate Financial Assistant")
    print(f"  {len(TEST_CASES)} questions  |  LLM Judge: Gemini 2.5 Flash")
    print(f"{'='*60}\n")

    results = []

    for tc in TEST_CASES:
        print(f"[{tc['id']:02d}/10] {tc['intent']:<25} {tc['question'][:55]}...")

        # Step 1: Get assistant answer (with backoff)
        t0 = time.time()
        answer = _call_with_backoff(
            call_llm,
            user_message=tc["question"],
            context_text=context_text,
            history=[],
            intent=tc["intent"],
        )
        latency = time.time() - t0

        # Pause between the two Gemini calls to respect 5 RPM free tier
        time.sleep(13)

        # Step 2: Judge the answer (with backoff)
        try:
            scores = _call_with_backoff(_judge_answer, tc["question"], context_text, answer, api_key)
            r = scores.get("relevance", 0)
            g = scores.get("groundedness", 0)
            h = scores.get("helpfulness", 0)
            avg = (r + g + h) / 3
            reason = scores.get("reason", "")
        except Exception as e:
            print(f"  !! Judge parse error: {e}")
            r = g = h = avg = 0
            reason = f"Judge error: {e}"

        print(f"         Rel={r}/5  Grnd={g}/5  Help={h}/5  Avg={avg:.2f}/5  [{latency:.1f}s]")
        if reason:
            print(f"         Reason: {reason}")

        results.append({
            "id": tc["id"],
            "intent": tc["intent"],
            "question": tc["question"],
            "answer": answer,
            "scores": {"relevance": r, "groundedness": g, "helpfulness": h},
            "average": round(avg, 3),
            "latency_s": round(latency, 2),
            "judge_reason": reason,
        })

        # Pause between questions to respect 5 RPM free tier
        time.sleep(13)

    # ── Aggregate results ────────────────────────────────────────────────────
    n = len(results)
    avg_rel  = sum(r["scores"]["relevance"]    for r in results) / n
    avg_grnd = sum(r["scores"]["groundedness"] for r in results) / n
    avg_help = sum(r["scores"]["helpfulness"]  for r in results) / n
    avg_all  = sum(r["average"]               for r in results) / n

    # Normalize to %
    relevance_pct    = round((avg_rel  / 5) * 100, 1)
    groundedness_pct = round((avg_grnd / 5) * 100, 1)
    helpfulness_pct  = round((avg_help / 5) * 100, 1)
    overall_pct      = round((avg_all  / 5) * 100, 1)

    # By intent
    intent_scores: dict[str, list] = {}
    for r in results:
        intent_scores.setdefault(r["intent"], []).append(r["average"])
    intent_avg = {k: round(sum(v)/len(v)/5*100, 1) for k, v in intent_scores.items()}

    print(f"\n{'='*60}")
    print("  EVALUATION RESULTS")
    print(f"{'='*60}")
    print(f"  Questions evaluated : {n}")
    print(f"  Relevance           : {avg_rel:.2f}/5  ({relevance_pct}%)")
    print(f"  Groundedness        : {avg_grnd:.2f}/5  ({groundedness_pct}%)")
    print(f"  Helpfulness         : {avg_help:.2f}/5  ({helpfulness_pct}%)")
    print(f"  --- OVERALL ---     : {avg_all:.2f}/5  ({overall_pct}%)")

    print(f"\n  By intent:")
    for intent, pct in sorted(intent_avg.items(), key=lambda x: -x[1]):
        bar = "█" * int(pct / 5)
        print(f"    {intent:<28} {pct:>5.1f}%  {bar}")

    # Weakest questions
    worst = sorted(results, key=lambda r: r["average"])[:3]
    print(f"\n  3 weakest answers:")
    for r in worst:
        print(f"    [{r['id']:02d}] {r['question'][:55]:<55} avg={r['average']:.2f}/5")

    print(f"{'='*60}\n")

    # ── Save ─────────────────────────────────────────────────────────────────
    report = {
        "summary": {
            "n_questions": n,
            "relevance_pct": relevance_pct,
            "groundedness_pct": groundedness_pct,
            "helpfulness_pct": helpfulness_pct,
            "overall_pct": overall_pct,
            "by_intent": intent_avg,
        },
        "questions": results,
    }
    out_path = ROOT / "scripts" / "rag_eval_results.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Results saved to: {out_path}\n")

    return overall_pct


if __name__ == "__main__":
    pct = run_evaluation()
    print(f"  Answer relevance: {pct}%\n")
