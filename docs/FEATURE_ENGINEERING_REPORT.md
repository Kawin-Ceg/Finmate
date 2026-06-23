# FinMate — Feature Engineering Benchmark Report

**Scripts:** `backend/scripts/benchmark_features.py`
**Dataset:** `transactions_train_v2.csv` (10,622 rows, see `DATASET_REPORT.md`)
**Classifier held fixed:** `LogisticRegression` (max_iter=2000) for every feature set, so results isolate the effect of *features*, not algorithm choice — that comparison is Phase 4.
**Evaluation:** Group-aware splitting by `brand` (see `DATASET_REPORT.md`, "Group-Aware Evaluation Design") — every number below measures generalization to merchants never seen during training, not formatting-robustness on known brands.

---

## A Methodology Correction Made Mid-Phase (worth stating upfront)

The first benchmark pass used a **single** 80/20 grouped split (one random seed) and showed "wider n-grams" (word 1-3, char 2-6) beating the current production config (word 1-2, char 3-5) by +0.91pp. Before recommending a change, I re-ran the comparison across 5 different split seeds — wider n-grams **lost** in 4 of 5, by margins up to 1.95pp. The original "win" was noise from one favorable split, not a real effect.

This is exactly the failure mode flagged earlier in this project (same-brand leakage inflating accuracy) wearing a different disguise: **a single train/test split, even a group-aware one, is not a reliable enough estimate when brand-group sizes are this uneven** (887 groups, 683 of them singletons — see `DATASET_REPORT.md`). Every result below uses proper **5-fold grouped cross-validation** (`GroupKFold`, grouped by `brand`) and reports mean ± standard deviation, not a single number.

---

## Results (5-fold grouped CV, mean accuracy ± std)

| Feature Set | Mean Accuracy | Std Dev | Mean Macro F1 |
|---|---|---|---|
| **Current production (word 1-2 + char 3-5 TF-IDF, normalized)** | **66.16%** | ±5.28% | 0.6507 |
| Wider n-grams (word 1-3, char 2-6) | 65.32% | ±5.10% | 0.6410 |
| Word n-grams only (no char n-grams) | 57.53% | ±4.46% | 0.6030 |
| Char n-grams only (no word n-grams) | 63.77% | ±6.37% | 0.6430 |
| No merchant normalization (raw text, prefixes kept) | 61.53% | ±6.59% | — |
| Current production + **synthetic** amount/transaction-type | 72.62% | ±6.23% | — |

The ±5-6% standard deviation across folds is itself an important, honest finding: it's a direct, measured confidence interval on held-out-brand accuracy that the original model never had (Phase 1 audit flagged "no documented confidence interval" as a weakness — this report produces one).

---

## Findings

1. **The current production feature set (word 1-2 + char 3-5 TF-IDF) is already the best text-only configuration tested.** Neither widening the n-gram ranges nor dropping either branch improves on it. **No change recommended here.**
2. **Char n-grams carry most of the signal** (63.77% alone vs. 57.53% for word n-grams alone) — expected for short, brand-substring-heavy, often-truncated bank narrations where character fragments (e.g., "swig", "amaz") generalize better than whole-word tokens to differently-formatted instances of the same brand. Word n-grams still add a real +2.39pp on top of char n-grams when combined — **keep both, as the current architecture already does.**
3. **Merchant normalization (`clean_merchant()` — stripping UPI/NEFT/IMPS/POS prefixes, digit sequences, punctuation) provides a real, robust ~4.6pp lift** (66.16% normalized vs. 61.53% raw). This is a genuine, validated win for code that was already in production but had never been benchmarked against its absence. **Confirmed: keep this preprocessing step.**
4. **Amount/transaction-type features show a large lift (+6.46pp) but it is not currently trustworthy** — the amount distributions are synthetic, designed by me with deliberately-overlapping-but-still-category-correlated lognormal parameters (see `benchmark_features.py` `AMOUNT_PARAMS`). A model exploiting a signal I invented is not evidence that signal exists in real transaction amounts. **Not adopted into the production default this phase.** See recommendation below for how to validate this for real.

## Embeddings — evaluated by reasoning, not by training one

The task asked to evaluate embeddings "if useful." Given finding #2 above — character n-grams (sub-word fragments) carry most of the discriminative signal on this data, not whole-word semantic meaning — this is a strong structural signal that dense sentence embeddings (designed to capture semantic/contextual meaning in natural language) are a poor fit for short, formulaic, reference-number-laden bank narrations like `UPI/SWIGGY/846891707`. Installing a sentence-transformers + torch stack (typically 1-2GB+ of dependencies, materially slower CPU inference) for a task where the dominant signal is "does this exact brand substring or a near-variant of it appear" is the textbook definition of unnecessary complexity the task explicitly asked to avoid. **Decision: skip embeddings, documented here rather than silently omitted.** If a future real-world dataset shows char-n-grams underperforming (e.g., once genuinely novel small/regional merchants dominate), this decision should be revisited.

## Recommendations Carried Into Phase 4

- **Feature set to use for all Phase 4 model benchmarking:** current production config — TF-IDF word(1-2, 6000 feat) + char(3-5, 12000 feat) `FeatureUnion` on `clean_merchant()`-normalized text. No changes.
- **New honest baseline to beat:** **66.16% ± 5.28%** (held-out-brand, 5-fold grouped CV) — not the old single-split 69.1%, and not any of the inflated single-seed numbers seen during this phase's own false start.
- **Amount/transaction-type features: deferred, with a concrete validation path.** The production `transactions` table already stores real user transactions with real amounts against real (ML- or rule-assigned) categories. Once there's a meaningful volume of real labeled transactions, the right move is to recompute actual amount-by-category distributions from that real data (replacing the synthetic `AMOUNT_PARAMS` lognormal guesses) and re-run this exact benchmark before deciding whether to ship the feature. The `FeatureUnion`/`ColumnTransformer` plumbing in `benchmark_features.py` is already written and ready for that swap.
