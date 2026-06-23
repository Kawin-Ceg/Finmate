#!/usr/bin/env python
"""
Feature Engineering Benchmark — FinMate ML Upgrade Phase 3

Compares candidate feature sets for the transaction categorizer using a
FIXED classifier (LogisticRegression) so the comparison isolates the effect
of features, not algorithm choice (that's Phase 4's job).

Evaluation uses a GROUP-AWARE split (grouped by `brand`, see
generate_synthetic_dataset.py) — entire brands are held out between train
and test, so the reported accuracy measures generalization to unseen
merchants, not memorization of brand substrings seen in a different
narration format. See DATASET_REPORT.md "Group-Aware Evaluation Design".

Usage:
    python scripts/benchmark_features.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from train_transaction_classifier import clean_merchant  # noqa: E402

BACKEND_DIR = SCRIPT_DIR.parent
DATA_PATH = BACKEND_DIR / "data" / "transactions_train_v2.csv"

RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Domain-informed SYNTHETIC amount distributions, used only to benchmark
# whether amount/transaction-type features are *structurally* useful.
# These ranges are deliberately overlapping across categories (not perfectly
# separable) to avoid a trivial/inflated result. They are NOT measured from
# real transactions — flagged loudly in the report, treat any lift from this
# feature set as directional only, pending validation on real amount data.
# ---------------------------------------------------------------------------
AMOUNT_PARAMS = {  # category: (log-mean, log-sigma) in INR
    "Food": (5.7, 0.7), "Transport": (5.0, 0.9), "Shopping": (6.7, 1.1),
    "Utilities": (6.4, 0.6), "Health": (6.2, 1.0), "Insurance": (8.9, 0.7),
    "Investment": (8.5, 1.2), "Income": (10.6, 0.6), "Education": (8.0, 1.0),
    "Rent": (9.4, 0.4), "Entertainment": (5.9, 0.8), "Subscriptions": (5.7, 0.6),
    "Transfers": (7.6, 1.4), "Cash": (7.6, 0.5), "Other": (5.3, 0.9),
}
CREDIT_CATEGORIES = {"Income"}


def synthesize_amount(category: str, rng: np.random.Generator) -> float:
    mu, sigma = AMOUNT_PARAMS[category]
    return float(np.clip(rng.lognormal(mu, sigma), 10, 500_000))


def synthesize_txn_type(category: str, rng: np.random.Generator) -> str:
    if category in CREDIT_CATEGORIES:
        return "credit"
    if category == "Transfers":
        return rng.choice(["credit", "debit"], p=[0.45, 0.55])
    if category == "Cash":
        return rng.choice(["credit", "debit"], p=[0.10, 0.90])
    return "debit"


def build_text_vectorizer(word_ngram=(1, 2), char_ngram=(3, 5), word_only=False, char_only=False):
    word_vec = TfidfVectorizer(
        analyzer="word", ngram_range=word_ngram, max_features=6000,
        sublinear_tf=True, min_df=1, token_pattern=r"\b[a-z][a-z]+\b",
    )
    char_vec = TfidfVectorizer(
        analyzer="char_wb", ngram_range=char_ngram, max_features=12000,
        sublinear_tf=True, min_df=1,
    )
    if word_only:
        return FeatureUnion([("word", word_vec)])
    if char_only:
        return FeatureUnion([("char", char_vec)])
    return FeatureUnion([("word", word_vec), ("char", char_vec)])


def evaluate(X_train_vec, X_test_vec, y_train, y_test) -> dict:
    clf = LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)
    clf.fit(X_train_vec, y_train)
    y_pred = clf.predict(X_test_vec)
    return {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "macro_f1": round(float(f1_score(y_test, y_pred, average="macro", zero_division=0)), 4),
    }


def main():
    df = pd.read_csv(DATA_PATH)
    le = LabelEncoder()
    df["label"] = le.fit_transform(df["category"])

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=RANDOM_STATE)
    train_idx, test_idx = next(splitter.split(df, groups=df["brand"]))
    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    overlap = set(train_df["brand"]) & set(test_df["brand"])
    print(f"Train: {len(train_df)} rows | Test: {len(test_df)} rows | Brand overlap: {len(overlap)} (must be 0)")
    assert len(overlap) == 0, "Group split leaked brands between train/test!"

    y_train, y_test = train_df["label"].values, test_df["label"].values

    results = {}

    # --- 1. Baseline: current production feature set, with normalization ---
    train_clean = train_df["merchant_name"].apply(clean_merchant)
    test_clean = test_df["merchant_name"].apply(clean_merchant)
    vec = build_text_vectorizer()
    Xtr, Xte = vec.fit_transform(train_clean), vec.transform(test_clean)
    results["1. Baseline (word+char TF-IDF, normalized)"] = evaluate(Xtr, Xte, y_train, y_test)

    # --- 2. No merchant normalization (raw text, no UPI/NEFT prefix strip) ---
    vec = build_text_vectorizer()
    Xtr, Xte = vec.fit_transform(train_df["merchant_name"]), vec.transform(test_df["merchant_name"])
    results["2. No normalization (raw merchant text)"] = evaluate(Xtr, Xte, y_train, y_test)

    # --- 3. Word n-grams only (drop char n-grams) ---
    vec = build_text_vectorizer(word_only=True)
    Xtr, Xte = vec.fit_transform(train_clean), vec.transform(test_clean)
    results["3. Word n-grams only"] = evaluate(Xtr, Xte, y_train, y_test)

    # --- 4. Char n-grams only (drop word n-grams) ---
    vec = build_text_vectorizer(char_only=True)
    Xtr, Xte = vec.fit_transform(train_clean), vec.transform(test_clean)
    results["4. Char n-grams only"] = evaluate(Xtr, Xte, y_train, y_test)

    # --- 5. Wider n-gram ranges (word 1-3, char 2-6) ---
    vec = build_text_vectorizer(word_ngram=(1, 3), char_ngram=(2, 6))
    Xtr, Xte = vec.fit_transform(train_clean), vec.transform(test_clean)
    results["5. Wider n-grams (word 1-3, char 2-6)"] = evaluate(Xtr, Xte, y_train, y_test)

    # --- 6. Baseline text + synthetic amount/transaction-type features ---
    rng = np.random.default_rng(RANDOM_STATE)
    for d in (train_df, test_df):
        d["amount"] = [synthesize_amount(c, rng) for c in d["category"]]
        d["txn_type"] = [synthesize_txn_type(c, rng) for c in d["category"]]
        d["log_amount"] = np.log1p(d["amount"])

    vec = build_text_vectorizer()
    Xtr_text, Xte_text = vec.fit_transform(train_clean), vec.transform(test_clean)

    scaler = StandardScaler()
    amt_tr = scaler.fit_transform(train_df[["log_amount"]])
    amt_te = scaler.transform(test_df[["log_amount"]])

    ohe = OneHotEncoder(handle_unknown="ignore")
    type_tr = ohe.fit_transform(train_df[["txn_type"]])
    type_te = ohe.transform(test_df[["txn_type"]])

    Xtr_combined = sparse.hstack([Xtr_text, sparse.csr_matrix(amt_tr), type_tr]).tocsr()
    Xte_combined = sparse.hstack([Xte_text, sparse.csr_matrix(amt_te), type_te]).tocsr()
    results["6. Baseline + SYNTHETIC amount + txn_type (directional only)"] = evaluate(
        Xtr_combined, Xte_combined, y_train, y_test
    )

    print(f"\n{'Feature Set':55s} {'Accuracy':>10s} {'Macro F1':>10s}")
    print("-" * 77)
    for name, metrics in results.items():
        print(f"{name:55s} {metrics['accuracy']*100:9.2f}% {metrics['macro_f1']:10.4f}")

    return results


if __name__ == "__main__":
    main()
