#!/usr/bin/env python
"""
Confidence Threshold Calibration — FinMate ML Upgrade Phase 5

Using the Phase 4 winner (determined from model_benchmark_results.json),
we test a range of confidence thresholds and report:
  - coverage      : fraction of predictions that PASS the threshold (not sent to fallback)
  - accuracy      : accuracy on the covered (confident) predictions only
  - fallback_rate : 1 - coverage (fraction routed to fallback/manual review)
  - precision     : same as accuracy on covered subset (no false-high-conf accepted)

The trade-off: a high threshold yields high precision on confident predictions but
pushes more transactions into a "low confidence" state (shown as "Other" or flagged
for user review). A threshold of 0.0 is equivalent to no threshold at all.

Evaluation is group-aware GroupKFold(5) on brand groups — same protocol as
Phase 3 and Phase 4.

Usage:
    python scripts/calibrate_confidence.py
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import LabelEncoder

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from train_transaction_classifier import clean_merchant  # noqa: E402
from benchmark_features import build_text_vectorizer  # noqa: E402

BACKEND_DIR = SCRIPT_DIR.parent
DATA_PATH = BACKEND_DIR / "data" / "transactions_train_v2.csv"
RESULTS_PATH = SCRIPT_DIR / "model_benchmark_results.json"
CALIBRATION_PATH = SCRIPT_DIR / "calibration_results.json"

RANDOM_STATE = 42
N_FOLDS = 5
THRESHOLDS = [0.0, 0.40, 0.50, 0.60, 0.70, 0.80]


def load_best_model():
    """Load the Phase 4 benchmark results and instantiate the winning model."""
    if not RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"{RESULTS_PATH} not found — run benchmark_models.py first (Phase 4)."
        )
    with open(RESULTS_PATH) as fh:
        results = json.load(fh)

    best_name = max(results, key=lambda n: results[n]["macro_f1_mean"])
    print(f"Phase 4 winner: {best_name}  (macro_f1={results[best_name]['macro_f1_mean']:.4f})")
    print(f"Accuracy: {results[best_name]['accuracy_mean']*100:.2f}% ± {results[best_name]['accuracy_std']*100:.2f}%\n")

    if best_name == "LightGBM":
        from lightgbm import LGBMClassifier
        return best_name, LGBMClassifier(
            n_estimators=300, random_state=RANDOM_STATE, n_jobs=-1, verbose=-1
        )
    if best_name == "XGBoost":
        from xgboost import XGBClassifier
        return best_name, XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8, eval_metric="mlogloss",
            random_state=RANDOM_STATE, n_jobs=-1, verbosity=0,
        )
    if best_name == "RandomForest":
        from sklearn.ensemble import RandomForestClassifier
        return best_name, RandomForestClassifier(
            n_estimators=300, random_state=RANDOM_STATE, n_jobs=-1
        )
    # default fallback: LR (also used as calibration base)
    return best_name, LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)


def evaluate_threshold(y_true, proba, threshold: float, n_classes: int) -> dict:
    """Compute metrics for predictions above the given confidence threshold."""
    max_prob = proba.max(axis=1)
    pred = proba.argmax(axis=1)
    mask = max_prob >= threshold

    coverage = float(mask.mean())
    fallback_rate = 1.0 - coverage

    if mask.sum() == 0:
        return {
            "threshold": threshold,
            "coverage": 0.0,
            "fallback_rate": 1.0,
            "accuracy_on_covered": None,
            "macro_f1_on_covered": None,
        }

    acc = float(accuracy_score(y_true[mask], pred[mask]))
    macro_f1 = float(
        f1_score(y_true[mask], pred[mask], average="macro",
                 labels=list(range(n_classes)), zero_division=0)
    )
    return {
        "threshold": threshold,
        "coverage": round(coverage, 4),
        "fallback_rate": round(fallback_rate, 4),
        "accuracy_on_covered": round(acc, 4),
        "macro_f1_on_covered": round(macro_f1, 4),
    }


def main():
    df = pd.read_csv(DATA_PATH)
    le = LabelEncoder()
    df["label"] = le.fit_transform(df["category"])
    df["clean"] = df["merchant_name"].apply(clean_merchant)
    n_classes = len(le.classes_)

    model_name, base_clf = load_best_model()

    # Wrap in Platt/isotonic calibration for reliable probability estimates.
    # LightGBM and tree-based models output uncalibrated probabilities; Platt
    # scaling (sigmoid method, default for CalibratedClassifierCV) corrects
    # overconfidence without changing the predicted class.
    clf = CalibratedClassifierCV(base_clf, cv=3, method="sigmoid")

    gkf = GroupKFold(n_splits=N_FOLDS)
    fold_splits = list(gkf.split(df, groups=df["brand"]))

    # Accumulate per-threshold results across all folds
    threshold_fold_results: dict[float, list[dict]] = {t: [] for t in THRESHOLDS}

    for fold_i, (train_idx, test_idx) in enumerate(fold_splits):
        tr, te = df.iloc[train_idx], df.iloc[test_idx]

        vec = build_text_vectorizer()
        Xtr = vec.fit_transform(tr["clean"])
        Xte = vec.transform(te["clean"])

        print(f"  Fitting fold {fold_i+1}/{N_FOLDS}...", end=" ", flush=True)
        import time; t0 = time.time()
        clf.fit(Xtr, tr["label"])
        proba = clf.predict_proba(Xte)
        print(f"{time.time()-t0:.1f}s")

        y_test = te["label"].values
        for thr in THRESHOLDS:
            r = evaluate_threshold(y_test, proba, thr, n_classes)
            threshold_fold_results[thr].append(r)

    # Average across folds
    summary = []
    for thr in THRESHOLDS:
        folds = threshold_fold_results[thr]
        accs = [f["accuracy_on_covered"] for f in folds if f["accuracy_on_covered"] is not None]
        f1s = [f["macro_f1_on_covered"] for f in folds if f["macro_f1_on_covered"] is not None]
        covs = [f["coverage"] for f in folds]
        summary.append({
            "threshold": thr,
            "mean_coverage": round(float(np.mean(covs)), 4),
            "mean_fallback_rate": round(1 - float(np.mean(covs)), 4),
            "mean_accuracy_on_covered": round(float(np.mean(accs)), 4) if accs else None,
            "std_accuracy_on_covered": round(float(np.std(accs)), 4) if accs else None,
            "mean_macro_f1_on_covered": round(float(np.mean(f1s)), 4) if f1s else None,
        })

    print(f"\n\n{'='*90}")
    print(f"Model: {model_name}  (Platt-calibrated)  |  5-fold GroupKFold by brand")
    print(f"{'='*90}")
    print(
        f"{'Threshold':>10s} {'Coverage':>10s} {'Fallback%':>10s} "
        f"{'Acc@Covered':>14s} {'MacroF1@Covered':>16s}"
    )
    print("-" * 90)
    for r in summary:
        fb_pct = r["mean_fallback_rate"] * 100
        cov_pct = r["mean_coverage"] * 100
        acc_str = f"{r['mean_accuracy_on_covered']*100:.2f}% ±{r['std_accuracy_on_covered']*100:.2f}%" if r["mean_accuracy_on_covered"] else "N/A"
        f1_str = f"{r['mean_macro_f1_on_covered']:.4f}" if r["mean_macro_f1_on_covered"] else "N/A"
        print(f"    >={r['threshold']:.2f}  {cov_pct:8.1f}%  {fb_pct:8.1f}%  {acc_str:>14s}  {f1_str:>16s}")

    with open(CALIBRATION_PATH, "w") as fh:
        json.dump({"model": model_name, "results": summary}, fh, indent=2)
    print(f"\nFull results saved to: {CALIBRATION_PATH}")

    return summary


if __name__ == "__main__":
    main()
