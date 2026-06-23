#!/usr/bin/env python
"""
Forecasting V2 Benchmark — FinMate ML Upgrade Phase 7

Benchmarks within-month budget-spend-projection algorithms:
  - Baseline: linear daily rate (current production algorithm)
  - HistoricalPrior: weighted average of same-category prior-month totals
  - BlendedRate: 60% daily rate + 40% historical prior (Bayesian-style)
  - LightGBM Regressor: day features + lag features
  - XGBoost Regressor: same feature set

The task: given partial-month spending (day K of month), predict the
total spend for the entire month.

Data: synthetically generated 36-month × 15-category spending series with
realistic trend, seasonal, and day-of-week effects. The generation is
intentionally conservative (moderate seasonality, realistic noise) to avoid
artificially favouring algorithms that exploit perfect seasonal patterns.

Evaluation:
  - Rolling-forward CV: train on months 1-24, validate on months 25-36
  - Tested at observation day = 7, 15, 22 (early/mid/late prediction)
  - Metric: MAPE (Mean Absolute Percentage Error)
  - Per-category breakdowns to check for category-specific weaknesses

Usage:
    python scripts/benchmark_forecasting.py
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).parent
RESULTS_PATH = SCRIPT_DIR / "forecast_benchmark_results.json"
RANDOM_STATE = 42

N_MONTHS = 36
TRAIN_MONTHS = 24
TEST_MONTHS = N_MONTHS - TRAIN_MONTHS  # 12

CATEGORIES = [
    "Food", "Transport", "Shopping", "Utilities", "Health",
    "Insurance", "Investment", "Income", "Education", "Rent",
    "Entertainment", "Subscriptions", "Transfers", "Cash", "Other"
]

# Base monthly spend (INR) per category — realistic Indian household profile
BASE_SPEND = {
    "Food": 8000, "Transport": 3500, "Shopping": 12000, "Utilities": 4000,
    "Health": 3000, "Insurance": 2000, "Investment": 15000, "Income": 0,
    "Education": 5000, "Rent": 18000, "Entertainment": 2500,
    "Subscriptions": 1200, "Transfers": 5000, "Cash": 3000, "Other": 2000,
}

# Month-of-year seasonal factors (index 0 = January)
SEASONAL = {
    "Shopping": [0.8, 0.8, 0.9, 1.0, 1.0, 0.9, 0.9, 1.0, 1.0, 1.1, 1.5, 1.5],
    "Food":     [1.0, 1.0, 1.0, 0.9, 0.9, 1.0, 1.0, 1.0, 1.0, 1.1, 1.1, 1.1],
    "Transport":[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.1, 1.1, 1.0, 1.0, 1.0],
    "Insurance":[1.8, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 1.8],
    "Investment":[1.1,1.1, 1.0, 1.2, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.2],
    "Education":[1.3, 1.0, 1.2, 1.2, 1.3, 0.8, 0.7, 1.2, 1.3, 1.0, 1.0, 0.9],
    "Entertainment":[1.0,0.9,1.0,1.0,1.0,1.1,1.1,1.0,1.0,1.1,1.1,1.2],
}

ANNUAL_TREND = 0.006  # +0.6% per month (≈7% per year)


def _seasonal_factor(category: str, month: int) -> float:
    """Month is 1-indexed."""
    return SEASONAL.get(category, [1.0] * 12)[month - 1]


def _day_weights(n_days: int, category: str, rng: np.random.Generator) -> np.ndarray:
    """
    Return per-day spend fractions that sum to 1.0.
    Rent: front-loaded (days 1-5). Insurance: day-1 lump.
    Shopping/Entertainment: slightly weekend-heavy.
    Others: roughly uniform with noise.
    """
    if category == "Rent":
        w = np.zeros(n_days)
        w[:3] = [0.5, 0.3, 0.2]
        return w
    if category == "Insurance":
        w = np.zeros(n_days)
        w[0] = 1.0
        return w
    w = rng.uniform(0.5, 1.5, n_days)
    if category in ("Shopping", "Entertainment", "Food"):
        for i in range(n_days):
            if (i + 1) % 7 in (6, 0):
                w[i] *= 1.4
    return w / w.sum()


def generate_monthly_series(rng: np.random.Generator) -> pd.DataFrame:
    """Generate synthetic daily spending for 36 months × 15 categories."""
    rows = []
    for m_idx in range(N_MONTHS):
        year = 2023 + m_idx // 12
        month = (m_idx % 12) + 1
        import calendar
        n_days = calendar.monthrange(year, month)[1]
        trend = (1 + ANNUAL_TREND) ** m_idx

        for cat in CATEGORIES:
            base = BASE_SPEND[cat]
            if base == 0:
                continue
            seasonal = _seasonal_factor(cat, month)
            noise = rng.lognormal(0, 0.10)  # ±10% log-normal noise
            total_month = base * seasonal * trend * noise

            day_w = _day_weights(n_days, cat, rng)
            for d in range(n_days):
                rows.append({
                    "month_idx": m_idx,
                    "year": year,
                    "month": month,
                    "day": d + 1,
                    "n_days": n_days,
                    "category": cat,
                    "daily_spend": round(total_month * day_w[d], 2),
                    "total_month": round(total_month, 2),
                })

    return pd.DataFrame(rows)


def make_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to monthly totals per category."""
    return (
        df.groupby(["month_idx", "year", "month", "n_days", "category"])["daily_spend"]
        .sum()
        .reset_index()
        .rename(columns={"daily_spend": "actual_total"})
    )


def make_partial_month_features(df: pd.DataFrame, obs_day: int) -> pd.DataFrame:
    """
    For each (month, category), sum spending up to `obs_day` and attach
    historical-lag features computed from prior months.
    """
    partial = (
        df[df["day"] <= obs_day]
        .groupby(["month_idx", "year", "month", "n_days", "category"])["daily_spend"]
        .sum()
        .reset_index()
        .rename(columns={"daily_spend": "spend_so_far"})
    )

    monthly = make_monthly_summary(df)
    partial = partial.merge(
        monthly[["month_idx", "category", "actual_total"]],
        on=["month_idx", "category"]
    )

    records = []
    for cat in CATEGORIES:
        if cat not in partial["category"].values:
            continue
        cat_partial = partial[partial["category"] == cat].sort_values("month_idx").reset_index(drop=True)
        cat_monthly = monthly[monthly["category"] == cat].sort_values("month_idx").reset_index(drop=True)

        for i, row in cat_partial.iterrows():
            m_idx = int(row["month_idx"])
            hist = cat_monthly[cat_monthly["month_idx"] < m_idx]["actual_total"]
            lag1 = float(hist.iloc[-1]) if len(hist) >= 1 else float(row["actual_total"])
            lag2 = float(hist.iloc[-2]) if len(hist) >= 2 else lag1
            lag3 = float(hist.iloc[-3]) if len(hist) >= 3 else lag2
            rolling3 = float(hist.iloc[-3:].mean()) if len(hist) >= 1 else float(row["actual_total"])

            records.append({
                **row.to_dict(),
                "obs_day": obs_day,
                "daily_rate": float(row["spend_so_far"]) / obs_day,
                "linear_proj": float(row["spend_so_far"]) / obs_day * float(row["n_days"]),
                "lag1": lag1,
                "lag2": lag2,
                "lag3": lag3,
                "rolling3_avg": rolling3,
                "month_of_year": int(row["month"]),
            })

    return pd.DataFrame(records)


# ─── Algorithm implementations ────────────────────────────────────────────────

def predict_linear(feat_row: dict) -> float:
    return feat_row["linear_proj"]


def predict_historical_prior(feat_row: dict) -> float:
    return feat_row["rolling3_avg"]


def predict_blended(feat_row: dict, alpha: float = 0.6) -> float:
    return alpha * feat_row["linear_proj"] + (1 - alpha) * feat_row["rolling3_avg"]


def train_ml(train_df: pd.DataFrame, model_type: str = "lightgbm") -> Any:
    feature_cols = ["obs_day", "spend_so_far", "daily_rate", "n_days",
                    "month_of_year", "lag1", "lag2", "lag3", "rolling3_avg"]
    X = train_df[feature_cols].values
    y = train_df["actual_total"].values

    if model_type == "lightgbm":
        from lightgbm import LGBMRegressor
        clf = LGBMRegressor(n_estimators=200, random_state=RANDOM_STATE, verbose=-1)
    else:
        from xgboost import XGBRegressor
        clf = XGBRegressor(n_estimators=200, random_state=RANDOM_STATE, verbosity=0)

    clf.fit(X, y)
    return clf, feature_cols


def predict_ml(clf, feat_row: dict, feature_cols: list) -> float:
    X = np.array([[feat_row[c] for c in feature_cols]])
    return float(clf.predict(X)[0])


# ─── Evaluation ───────────────────────────────────────────────────────────────

def mape(actual: np.ndarray, pred: np.ndarray) -> float:
    mask = actual > 0
    return float(np.mean(np.abs((actual[mask] - pred[mask]) / actual[mask])) * 100)


def run_benchmark() -> dict:
    rng = np.random.default_rng(RANDOM_STATE)
    df = generate_monthly_series(rng)

    results = {}
    obs_days = [7, 15, 22]

    for obs_day in obs_days:
        print(f"\n--- Observation day: {obs_day} ---")
        feat_df = make_partial_month_features(df, obs_day)

        # Filter out months with no prior (can't compute lag features reliably until month 3+)
        feat_df = feat_df[feat_df["month_idx"] >= 3].reset_index(drop=True)

        train_df = feat_df[feat_df["month_idx"] < TRAIN_MONTHS]
        test_df = feat_df[feat_df["month_idx"] >= TRAIN_MONTHS]

        # Train ML models on training months
        lgbm_clf, feat_cols = train_ml(train_df, "lightgbm")
        xgb_clf, _ = train_ml(train_df, "xgboost")

        algo_preds: dict[str, list[float]] = {
            "LinearDailyRate": [],
            "HistoricalPrior(3mo)": [],
            "Blended(60/40)": [],
            "LightGBM": [],
            "XGBoost": [],
        }
        actuals: list[float] = []

        for _, row in test_df.iterrows():
            r = row.to_dict()
            algo_preds["LinearDailyRate"].append(predict_linear(r))
            algo_preds["HistoricalPrior(3mo)"].append(predict_historical_prior(r))
            algo_preds["Blended(60/40)"].append(predict_blended(r))
            algo_preds["LightGBM"].append(predict_ml(lgbm_clf, r, feat_cols))
            algo_preds["XGBoost"].append(predict_ml(xgb_clf, r, feat_cols))
            actuals.append(r["actual_total"])

        actual_arr = np.array(actuals)
        day_results = {}
        for name, preds in algo_preds.items():
            pred_arr = np.array(preds)
            err = mape(actual_arr, pred_arr)
            day_results[name] = round(err, 2)
            print(f"  {name:25s}  MAPE={err:.2f}%")

        # Per-category MAPE for winner vs baseline
        print(f"\n  Per-category MAPE (LinearDailyRate vs LightGBM):")
        per_cat = {}
        for cat in CATEGORIES:
            cat_mask = test_df["category"] == cat
            if cat_mask.sum() == 0:
                continue
            cat_test = test_df[cat_mask]
            cat_actual = cat_test["actual_total"].values
            cat_linear = np.array([predict_linear(r) for _, r in cat_test.iterrows()])
            cat_lgbm = np.array([predict_ml(lgbm_clf, r.to_dict(), feat_cols) for _, r in cat_test.iterrows()])
            m_lin = mape(cat_actual, cat_linear)
            m_lgbm = mape(cat_actual, cat_lgbm)
            per_cat[cat] = {"LinearDailyRate": round(m_lin, 2), "LightGBM": round(m_lgbm, 2)}
            delta = m_lin - m_lgbm
            sign = "-" if delta > 0 else "+"
            print(f"    {cat:15s}  Linear={m_lin:5.1f}%  LightGBM={m_lgbm:5.1f}%  ({sign}{abs(delta):.1f}pp)")

        results[f"day_{obs_day}"] = {"summary": day_results, "per_category": per_cat}

    return results


def main():
    print("FinMate — Forecasting V2 Benchmark (Phase 7)")
    print("=" * 60)
    print(f"Training months: {TRAIN_MONTHS}  |  Test months: {TEST_MONTHS}")
    print(f"Categories: {len(CATEGORIES)}  |  Observation days: 7, 15, 22")

    results = run_benchmark()

    print(f"\n\n{'='*65}")
    print(f"{'Algorithm':25s} {'Day 7 MAPE':>12s} {'Day 15 MAPE':>12s} {'Day 22 MAPE':>12s}")
    print("-" * 65)
    algo_names = ["LinearDailyRate", "HistoricalPrior(3mo)", "Blended(60/40)", "LightGBM", "XGBoost"]
    for name in algo_names:
        d7 = results["day_7"]["summary"].get(name, float("nan"))
        d15 = results["day_15"]["summary"].get(name, float("nan"))
        d22 = results["day_22"]["summary"].get(name, float("nan"))
        print(f"{name:25s} {d7:>11.2f}% {d15:>11.2f}% {d22:>11.2f}%")

    with open(RESULTS_PATH, "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nFull results saved to: {RESULTS_PATH}")

    return results


if __name__ == "__main__":
    main()
