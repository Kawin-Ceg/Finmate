from statistics import mean, stdev


def compute_health_score(transactions):
    income = sum(t.amount for t in transactions if t.transaction_type == "credit")
    expense = sum(t.amount for t in transactions if t.transaction_type == "debit")

    # Savings Rate — 35 pts (30% savings rate = full score)
    if income > 0:
        savings_rate = (income - expense) / income * 100
        sr_score = min(35.0, max(0.0, savings_rate * 35 / 30))
    else:
        savings_rate = 0.0
        sr_score = 0.0

    # Expense Stability — 25 pts (low CV = stable)
    monthly_expense: dict[str, float] = {}
    for t in transactions:
        if t.transaction_type == "debit":
            key = t.date.strftime("%Y-%m")
            monthly_expense[key] = monthly_expense.get(key, 0.0) + t.amount

    exp_months = list(monthly_expense.values())
    exp_cv = 0.0
    if len(exp_months) >= 2:
        exp_mean = mean(exp_months)
        exp_cv = stdev(exp_months) / exp_mean if exp_mean > 0 else 1.0
        exp_score = max(0.0, 25.0 * (1 - min(1.0, exp_cv)))
    elif len(exp_months) == 1:
        exp_score = 20.0
    else:
        exp_score = 0.0

    # Income Consistency — 25 pts (low CV = consistent)
    monthly_income: dict[str, float] = {}
    for t in transactions:
        if t.transaction_type == "credit":
            key = t.date.strftime("%Y-%m")
            monthly_income[key] = monthly_income.get(key, 0.0) + t.amount

    inc_months = list(monthly_income.values())
    inc_cv = 0.0
    if len(inc_months) >= 2:
        inc_mean = mean(inc_months)
        inc_cv = stdev(inc_months) / inc_mean if inc_mean > 0 else 1.0
        inc_score = max(0.0, 25.0 * (1 - min(1.0, inc_cv)))
    elif len(inc_months) == 1:
        inc_score = 20.0
    else:
        inc_score = 0.0

    # Category Diversification — 15 pts (HHI: lower = better)
    cat_totals: dict[str, float] = {}
    for t in transactions:
        if t.transaction_type == "debit":
            cat_totals[t.category] = cat_totals.get(t.category, 0.0) + t.amount

    if cat_totals:
        total_exp = sum(cat_totals.values())
        hhi = sum((v / total_exp) ** 2 for v in cat_totals.values()) if total_exp > 0 else 1.0
        div_score = max(0.0, 15.0 * (1 - hhi))
    else:
        div_score = 0.0

    total_score = max(0, min(100, int(round(sr_score + exp_score + inc_score + div_score))))

    if total_score >= 90:
        grade, status = "A+", "Excellent"
    elif total_score >= 80:
        grade, status = "A", "Very Good"
    elif total_score >= 70:
        grade, status = "B", "Good"
    elif total_score >= 60:
        grade, status = "C", "Fair"
    else:
        grade, status = "D", "Needs Improvement"

    insights = []

    if savings_rate >= 25:
        insights.append(f"Excellent savings habit — you're saving {savings_rate:.0f}% of your income.")
    elif savings_rate >= 10:
        insights.append(f"Savings rate of {savings_rate:.0f}%. Aim for 20%+ for long-term security.")
    elif income > 0:
        insights.append("Savings rate is under 10%. Review your top spending categories.")

    if len(exp_months) >= 2:
        if exp_cv > 0.35:
            insights.append("Monthly expenses fluctuate significantly. A budget can help stabilize spending.")
        else:
            insights.append("Monthly expenses are consistent — a sign of disciplined spending.")

    if len(inc_months) >= 2:
        if inc_cv < 0.15:
            insights.append("Income is highly consistent — strong financial foundation.")
        elif inc_cv > 0.4:
            insights.append("Irregular income detected. Building an emergency fund is recommended.")

    if cat_totals and expense > 0:
        top_cat = max(cat_totals, key=lambda k: cat_totals[k])
        top_pct = cat_totals[top_cat] / expense * 100
        if top_pct > 40:
            insights.append(f"{top_cat} accounts for {top_pct:.0f}% of expenses — check if this is intentional.")

    weekend_amts = [
        t.amount for t in transactions
        if t.transaction_type == "debit" and t.date.weekday() >= 5
    ]
    weekday_amts = [
        t.amount for t in transactions
        if t.transaction_type == "debit" and t.date.weekday() < 5
    ]
    if weekend_amts and weekday_amts:
        avg_wknd = sum(weekend_amts) / len(weekend_amts)
        avg_wkdy = sum(weekday_amts) / len(weekday_amts)
        if avg_wknd > avg_wkdy * 1.5:
            insights.append(
                f"Weekend spending is {avg_wknd / avg_wkdy:.1f}× higher than weekday average."
            )

    return {
        "score": total_score,
        "grade": grade,
        "status": status,
        "breakdown": {
            "savings_rate": round(sr_score, 1),
            "savings_rate_max": 35,
            "expense_stability": round(exp_score, 1),
            "expense_stability_max": 25,
            "income_consistency": round(inc_score, 1),
            "income_consistency_max": 25,
            "diversification": round(div_score, 1),
            "diversification_max": 15,
        },
        "insights": insights[:5],
    }
