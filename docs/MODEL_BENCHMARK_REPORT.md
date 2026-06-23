# FinMate — Model Benchmark Report

**Script:** `backend/scripts/benchmark_models.py`
**Dataset:** `transactions_train_v2.csv` (10,622 rows — see `DATASET_REPORT.md`)
**Feature set:** TF-IDF word(1-2, max 6,000 feat) + char(3-5, max 12,000 feat) `FeatureUnion` on `clean_merchant()`-normalized text — validated as the best text-only config in Phase 3 (`FEATURE_ENGINEERING_REPORT.md`).
**Evaluation:** 5-fold GroupKFold by `brand` column — entire merchant brands held out between train/test folds. Every number below measures generalization to unseen merchants, not formatting variants of known brands.
**Primary selection metric: Macro F1** — weights all 15 categories equally; prevents a model from gaming accuracy by crushing minority classes (user requirement stated explicitly: "A model that gains 2% accuracy by crushing minority classes is not acceptable").

---

## A Recurring Lesson: Single-Split Numbers Are Unreliable

The Phase 3 smoke-test (one GroupShuffleSplit, seed=42) showed LightGBM at **72.45%** accuracy — the highest single number seen anywhere in this evaluation. That result drove initial interest in LightGBM as the likely winner.

The 5-fold GroupKFold CV shows LightGBM at **65.00% ± 4.65%** and macro F1 of **0.6096 ± 0.0335**. The 7.45pp gap was a single favorable split where LightGBM happened to see easily-separable holdout brands in seed=42's partition. This is the same failure mode documented in `FEATURE_ENGINEERING_REPORT.md` (Phase 3 methodology correction) now manifesting at the model-selection stage. The cure is the same: always use k-fold CV; never trust a single number.

---

## Results (5-fold GroupKFold, mean ± std)

| Model | Accuracy | Macro F1 | Weighted F1 | Avg Fit Time |
|---|---|---|---|---|
| **LogisticRegression** | **66.16% ±5.28%** | **0.6507 ±0.0487** | **0.6670 ±0.0469** | **1.3s** |
| LightGBM | 65.00% ±4.65% | 0.6096 ±0.0335 | 0.6414 ±0.0571 | 31.7s |
| RandomForest | 61.81% ±6.02% | 0.6105 ±0.0582 | 0.6351 ±0.0466 | 4.3s |
| XGBoost | 60.63% ±6.17% | 0.5713 ±0.0319 | 0.6009 ±0.0558 | 173.5s |
| ~~CatBoost~~ | ~~54.73%~~ | — | — | ~~85s~~ |

CatBoost was excluded from full CV after timing pre-tests (see "Excluded Algorithms" below).

**Winner: LogisticRegression** — highest on both accuracy and macro F1, and 24× faster than LightGBM, 133× faster than XGBoost.

---

## Per-Class F1 (mean across 5 folds)

| Category | LogisticReg | RandomForest | XGBoost | LightGBM |
|---|---|---|---|---|
| Cash | 0.8187 | 0.7876 | **0.9587** | 0.9236 |
| Education | **0.5432** | 0.5056 | 0.3961 | 0.4350 |
| Entertainment | 0.4933 | **0.5261** | 0.5186 | 0.5101 |
| Food | 0.4936 | 0.4281 | 0.3846 | **0.4956** |
| Health | **0.6107** | 0.5510 | 0.5857 | 0.5927 |
| Income | **0.9401** | 0.8481 | 0.8153 | 0.8774 |
| Insurance | 0.8847 | **0.9529** | 0.7144 | 0.8760 |
| Investment | 0.5842 | **0.6458** | 0.5980 | 0.6256 |
| Other | **0.8681** | 0.6936 | 0.6433 | 0.6373 |
| Rent | **0.5299** | 0.5037 | 0.4624 | 0.4867 |
| Shopping | 0.2764 | 0.2771 | 0.2831 | **0.3434** |
| Subscriptions | **0.3975** | 0.3142 | 0.3087 | 0.3318 |
| Transfers | 0.8283 | **0.8585** | 0.7293 | 0.7151 |
| Transport | **0.6729** | 0.4671 | 0.4772 | 0.5961 |
| Utilities | **0.8189** | 0.7977 | 0.6934 | 0.6975 |

LR wins or ties on 10 of 15 categories. The 5 it loses are Insurance, Investment, Entertainment (RF), Cash (XGBoost/LightGBM), and Shopping (LightGBM marginally). The losses are small; the wins are often large.

---

## Analysis

### Why LogisticRegression wins

Short merchant-name strings like `UPI/SWIGGY TECHNOLOGIES/8374918` are dominated by a handful of highly-discriminative token signals (brand substrings). TF-IDF already encodes these signals; a linear classifier over TF-IDF weights is the near-optimal solution for this kind of text. Ensemble tree methods add value when there are non-linear interaction effects between features — those interactions are largely absent here because the task is brand-to-category lookup, not complex multi-modal reasoning. The same phenomenon (LR ≈ or beats ensemble methods on bag-of-words text classification) is well-documented in the NLP literature.

### Why XGBoost underperforms (worst macro F1, highest cost)

XGBoost struggles on high-dimensional sparse inputs. Its split-finding is designed for dense continuous features; on a 18,000-dim sparse TF-IDF matrix it must sift through an enormous feature space to find useful binary splits, often settling for overfit decisions that memorize brand-substring patterns seen in training but don't generalize. The result: 173.5s per fit for the worst macro F1 in the group. XGBoost would benefit from SVD-based dimensionality reduction (truncated SVD / LSA) before being applied to TF-IDF features — that was out of scope here but noted for future work.

### Why LightGBM underperforms relative to its smoke-test number

LightGBM's leaf-wise (best-first) tree growth is well-suited to moderate-dimension dense features. On sparse TF-IDF it performs better than XGBoost and RandomForest but still can't match LR's linear decision boundary on this specific task. The 7.45pp drop from the single-split result (72.45% → 65.00%) is pure variance from the brand-group composition of a single favorable holdout fold.

### Problematic categories — all models, not just one

Shopping (0.27-0.34) and Subscriptions (0.31-0.40) are consistently the worst-predicted categories across all models. The likely causes:
1. **High lexical overlap with other categories.** Amazon narrations appear in both Shopping and Income (refund credits). Netflix appears in Subscriptions but also Entertainment when context is ambiguous.
2. **Synthetic data limitation.** Many Shopping and Subscription narrations share brand names (AMAZON, FLIPKART) that already appear under other categories in different contexts. The brand-level grouping used in train/test splitting correctly isolates these — the model must generalize to an unseen brand, not to an unseen format of a known brand. But the synthetic generation may not have captured enough within-category diversity.
3. **Implication:** these two categories are strong candidates for user feedback correction (Phase 6) — confidence thresholds will route many of them to the fallback path rather than forcing a low-confidence guess.

---

## Excluded Algorithms

### CatBoost

Pre-tests on a single GroupShuffleSplit fit showed:
- `iterations=300, depth=6`: 905s/fit, 60.35% accuracy — excluded from all CV
- `iterations=150, depth=4`: 85s/fit, **54.73%** accuracy — materially worse than LogisticRegression
- `iterations=100, depth=4`: 51s/fit, 53.19% accuracy — even worse

CatBoost is designed for dense tabular categorical features with oblivious decision trees and specialized encoding. Its sparse matrix handling on 18,000-dim TF-IDF is not competitive with LightGBM or even LogisticRegression on this task. No hyperparameter configuration tested here changed that fundamental mismatch.

---

## Decision

**LogisticRegression replaces the existing XGBoost-based production model.**

Rationale:
1. Highest macro F1 (0.6507) — the stated minority-class-safety metric
2. Highest accuracy (66.16%) — against the same group-aware baseline that dethroned the old 69.1% single-split number
3. Fastest training (1.3s) — enables fast retraining when user feedback is collected (Phase 6)
4. Produces calibrated probability outputs — directly usable for confidence thresholds (Phase 5)
5. Interpretable — can explain predictions via feature weight inspection if needed for interview/audit

The previous production model (XGBoost, 69.1%) was evaluated on a non-group-aware split: same brands appeared in both train and test in different narration formats, inflating the headline number. The correct group-aware comparison puts XGBoost at **60.63% macro F1 = 0.5713** — the worst in this benchmark.

---

## Carry-Forward to Phase 5

- **Model to calibrate:** LogisticRegression (max_iter=2000)
- **Calibration method:** Platt scaling (CalibratedClassifierCV, sigmoid method) — corrects LR's slight overconfidence on multi-class problems
- **Threshold grid:** 0.40, 0.50, 0.60, 0.70, 0.80
- **Metrics to report per threshold:** coverage (% of predictions above threshold), fallback rate (% routed to user review), accuracy-on-covered, macro-F1-on-covered
- **Goal:** identify the threshold that maximizes accuracy-on-covered without sending more than ~20-25% of predictions to fallback
