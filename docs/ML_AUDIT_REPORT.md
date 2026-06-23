# FinMate — ML Systems Audit Report

**Date:** 2026-06-16
**Scope:** Transaction categorization engine + forecasting engine. Pre-implementation audit only — no code changed in this pass.

---

## 1. Transaction Categorization — Current Architecture

**Pipeline:** `clean_merchant()` → TF-IDF `FeatureUnion` (word 1-2grams, 6,000 features + char 3-5grams, 12,000 features = 18,000 total) → `XGBClassifier` (300 trees, depth 6) → `predict_proba()` → confidence-gated rule-based fallback.

**Files:** `scripts/train_transaction_classifier.py` (training), `app/services/ml_categorizer.py` (inference), `app/services/categorizer.py` (keyword fallback for 14 categories).

**Current metrics** (`models/training_report.json`):

| Metric | Value |
|---|---|
| Algorithm | XGBoost |
| Accuracy | 69.1% |
| Train / Test split | 711 / 178 (80/20, stratified) |
| Categories | 15 |
| Confidence threshold | 0.60 (hardcoded) |

**Per-class F1 (weakest 5):**

| Category | F1 | Support |
|---|---|---|
| Other | 0.250 | 5 |
| Health | 0.552 | 13 |
| Shopping | 0.588 | 16 |
| Subscriptions | 0.609 | 12 |
| Entertainment | 0.636 | 11 |

**Strongest 3:** Insurance (0.909), Cash (0.889), Investment (0.875) — all categories with a small, distinctive, low-variance keyword vocabulary (LIC/policy/premium, ATM/withdrawal, Zerodha/Groww/SIP).

### Weaknesses

1. **Dataset size (889 rows, 711 train).** With 18,000 TF-IDF features and only 711 training rows, the feature-to-sample ratio is roughly 25:1 — the model is almost certainly overfitting to the specific merchant strings present rather than learning generalizable category-discriminating patterns. This is the single biggest ceiling on accuracy; no amount of algorithm tuning fixes a data-starved high-dimensional fit.
2. **No cross-validation anywhere in the pipeline.** A single 80/20 stratified split means the reported 69.1% accuracy has no confidence interval — it could be ±5-10% on a different random split given how small the test set is (178 rows / 15 classes ≈ 12 per class on average, and several classes have single-digit support in the test fold).
3. **No hyperparameter search.** `n_estimators=300, max_depth=6, learning_rate=0.1` were chosen once and never tuned against held-out data.
4. **Algorithm choice was never benchmarked against alternatives.** XGBoost was selected because "it was specified as a hard requirement" per the existing ML documentation, not because it outperformed Logistic Regression, Random Forest, or LightGBM on this data. For sparse, low-sample, high-dimensional bag-of-n-grams data, simpler linear models (Logistic Regression with L2) frequently match or beat gradient boosting — this needs to be measured, not assumed.
5. **Confidence threshold (0.60) was chosen "empirically"** per the existing docs, with no documented sweep across alternative thresholds or measurement of the precision/coverage tradeoff at each.
6. **No feedback loop.** If a user manually corrects a miscategorized transaction today, that correction is not captured anywhere — it doesn't improve the model, and the same merchant will be miscategorized again on the next upload.
7. **English/Latin-script only.** `_clean()`'s regex strips anything that isn't `[a-z\s]`, so merchant names with regional-language characters are reduced to whitespace.

### Dataset Limitations (`data/transactions_train.csv`)

- 889 rows is hand-authored/curated (per the existing ML docs), not sourced from real transaction logs — so it reflects the author's mental model of "typical" merchant strings, not the actual messy distribution of real bank CSV exports (OCR artifacts, inconsistent casing, bank-specific abbreviations, truncated merchant names, regional merchants).
- Category balance ranges from 36 (Other) to 113 (Food) samples — a ~3:1 imbalance that's mild but still measurable in the per-class F1 spread above.
- Single source — no diversity of "voice" (e.g., different banks format UPI narrations differently: HDFC vs ICICI vs SBI prefix/suffix conventions are not represented).

---

## 2. Forecasting Engine — Current Architecture

**Files:** `app/services/budget_service.py` (`compute_forecast`), consumed by `app/routes/budgets.py`, `app/services/anomaly_service.py` (`detect_budget_risk_anomalies`), `app/services/context_builder.py` (Mate's budget context).

**Current method — linear daily-rate extrapolation:**
```python
daily_rate = current_month_spend / days_elapsed
projected_spend = daily_rate * days_in_month
overrun = max(0, projected_spend - monthly_limit)
risk = "exceeded" if pct >= 100 else "high" if pct >= 85 else "watch" if pct >= 60 else "safe"
```

### Weaknesses

1. **No historical learning whatsoever.** The forecast for category X this month uses only this month's spend-so-far — it never looks at how category X behaved in prior months (seasonality, recurring large payments like annual insurance premiums, paycheck-driven spending spikes).
2. **No uncertainty quantification.** A single point estimate (`projected_spend`) is presented as if it were certain. Early in the month (e.g., day 3 of 30), `daily_rate` is extrapolated from a tiny, high-variance sample — the existing code has no mechanism to express "this projection is unreliable this early in the month."
3. **No probability of exceeding budget.** Risk is a 4-bucket categorical label (safe/watch/high/exceeded) derived from a single deterministic percentage threshold, not a calibrated probability.
4. **No explainability beyond the number itself.** The forecast doesn't say *why* it's elevated (e.g., "driven by a one-time large purchase" vs. "sustained higher daily spending").
5. **Health score (`health_score_service.py`) is a separate, parallel statistical system** (savings rate, expense-CV, income-CV, category-HHI) that doesn't share any infrastructure with the forecaster — there's no unified "predictive" layer in the app at all today; everything is descriptive statistics computed fresh on every request.
6. **Anomaly detection (`anomaly_service.py`) is also purely statistical** (z-score, IQR, coefficient-of-variation thresholds) — legitimate and reasonably sound for what it does, but it's a different paradigm again (unsupervised outlier detection, not supervised forecasting), so "Forecasting V2" needs to decide how much it should unify with vs. stay separate from the anomaly engine's existing historical-aggregation logic (`_historical_transactions`, `_current_month_transactions` helpers it already has).

### Data Available for Forecasting

Per-user, the only features available are: `date`, `merchant`, `amount`, `transaction_type`, `category` (ML-assigned or rule-assigned), plus derived budget/anomaly state. There is **no external macro data** (no income verification, no recurring-payment calendar, no merchant metadata beyond the string itself). Any forecasting model is necessarily built on a single user's own transaction history — meaning **users with fewer than ~2-3 months of data will have very little signal for any model that relies on monthly seasonality**, a real constraint that needs to shape model choice (e.g., Prophet's strength — multi-season decomposition — is wasted on a typical new user with 3-6 weeks of history).

---

## 3. Improvement Opportunities (carried into later phases)

| Area | Opportunity |
|---|---|
| Categorization data | Expand sample count by an order of magnitude; diversify merchant string "voice" |
| Categorization features | Benchmark amount-bucket and transaction-type features alongside text n-grams |
| Categorization model | Benchmark Logistic Regression, Random Forest, XGBoost, LightGBM, CatBoost — don't assume the incumbent wins |
| Confidence threshold | Sweep 0.50/0.60/0.70/0.80 against actual precision/coverage, not a single anecdotal value |
| Feedback loop | Capture user corrections so the next retrain has real labeled signal, not just synthetic/sourced data |
| Forecasting | Move from point-estimate daily-rate extrapolation to a model with confidence intervals and exceed-probability, while being realistic about per-user data scarcity |
| Explainability | Surface *why* a forecast moved, not just the number |

---

## 4. Key Constraint to Flag Before Phase 2

A WebSearch pass for real, publicly available datasets matching "merchant name → spending category" in the Indian/UPI context found:
- No ready-made Kaggle dataset with Indian merchant narrations labeled into a category taxonomy resembling FinMate's 15 categories. Indian UPI datasets on Kaggle are either unlabeled (just amount/date/counterparty) or synthetic person-to-person transfer simulations.
- The closest legitimate real-world fit is US-centric credit-card transaction datasets with merchant-category-code-style labels (e.g., `priyamchoksi/credit-card-transactions-dataset`, ~1.85M rows, categories like `grocery_pos`, `gas_transport`, `health_fitness`, `entertainment`, `misc_pos`) — these map reasonably well onto FinMate's general categories (Food, Transport, Health, Entertainment, Shopping) but contain **zero examples** of India-specific categories that have no US equivalent in the same form (Insurance via LIC-style policies, Investment via Zerodha/Groww/UPI SIPs, UPI/NEFT/IMPS transfer prefixes, Indian Cash/ATM banking phrasing).
- Downloading any Kaggle dataset programmatically requires Kaggle API credentials (a `kaggle.json` token), which I don't have access to.

This directly affects whether Phase 2's "70-90% real data" target is achievable as stated, and needs a decision before dataset work starts — covered in the follow-up question alongside this report.
