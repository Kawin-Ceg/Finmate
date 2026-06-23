#!/usr/bin/env python
"""
Transaction Category Classifier — Training Pipeline

Usage:
    python scripts/train_transaction_classifier.py
    python scripts/train_transaction_classifier.py --dataset path/to/custom.csv

Dataset format (CSV):
    merchant_name,category

Artifacts saved to:
    models/transaction_model.pkl
    models/vectorizer.pkl
    models/label_encoder.pkl
    models/training_report.json

To replace with a real Kaggle dataset:
    1. Download a transaction categorization dataset from Kaggle
    2. Rename/map columns to 'merchant_name' and 'category'
    3. Run: python scripts/train_transaction_classifier.py --dataset path/to/kaggle_data.csv
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import LabelEncoder

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
MODELS_DIR = BACKEND_DIR / "models"

_PREFIX_RE = re.compile(
    r"^(upi[-/\s]?|neft[-/\s]?|imps[-/\s]?|nach[-/\s]?|ecs[-/\s]?|"
    r"rtgs[-/\s]?|pos[-/\s]?|aeps[-/\s]?|ach[-/\s]?|cdm[-/\s]?|atm[-/\s]?)",
    re.IGNORECASE,
)
_NUMBER_RE = re.compile(r"\b\d{5,}\b")
_NON_ALPHA_RE = re.compile(r"[^a-z\s]")
_WHITESPACE_RE = re.compile(r"\s+")


def clean_merchant(text: str) -> str:
    """Normalize merchant name for feature extraction."""
    text = str(text).lower().strip()
    text = _PREFIX_RE.sub("", text)
    text = _NUMBER_RE.sub("", text)
    text = _NON_ALPHA_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def load_dataset(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    required = {"merchant_name", "category"}
    if not required.issubset(df.columns):
        raise ValueError(
            f"Dataset must have columns: {required}. Found: {list(df.columns)}"
        )

    df = df.dropna(subset=["merchant_name", "category"])
    df["merchant_name"] = df["merchant_name"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df = df[(df["merchant_name"] != "") & (df["category"] != "")].reset_index(drop=True)

    logger.info(
        "Loaded %d samples | %d categories",
        len(df),
        df["category"].nunique(),
    )
    for cat, count in df["category"].value_counts().items():
        logger.info("  %-20s %d samples", cat, count)

    return df


def build_vectorizer() -> FeatureUnion:
    """
    Combined TF-IDF: word n-grams (1-2) + character n-grams (3-5).
    Character n-grams capture partial brand names and typos.
    Word n-grams capture multi-word phrases like 'uber pool'.
    """
    word_vec = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        max_features=6000,
        sublinear_tf=True,
        min_df=1,
        token_pattern=r"\b[a-z][a-z]+\b",
    )
    char_vec = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        max_features=12000,
        sublinear_tf=True,
        min_df=1,
    )
    return FeatureUnion([("word", word_vec), ("char", char_vec)])


def train(dataset_path: Path) -> dict:
    MODELS_DIR.mkdir(exist_ok=True)

    df = load_dataset(dataset_path)
    df["cleaned"] = df["merchant_name"].apply(clean_merchant)

    le = LabelEncoder()
    y = le.fit_transform(df["category"].values)

    # Use group-aware split when brand column is present (v2 dataset onwards).
    # This matches the evaluation protocol used in Phase 3/4 benchmarks and
    # produces a test accuracy that reflects generalization to unseen merchants.
    if "brand" in df.columns:
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        train_idx, test_idx = next(splitter.split(df, groups=df["brand"]))
        X_train = df["cleaned"].values[train_idx]
        X_test = df["cleaned"].values[test_idx]
        y_train = y[train_idx]
        y_test = y[test_idx]
        split_type = "group-aware (brand-held-out)"
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            df["cleaned"].values, y, test_size=0.2, random_state=42, stratify=y
        )
        split_type = "stratified random"

    logger.info("Train: %d  |  Test: %d  |  Split: %s", len(X_train), len(X_test), split_type)

    vectorizer = build_vectorizer()
    logger.info("Fitting TF-IDF vectorizer ...")
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # Phase 4 benchmark winner: LogisticRegression outperforms XGBoost, LightGBM,
    # and RandomForest on macro F1 (group-aware 5-fold CV) on this sparse TF-IDF
    # feature space. Wrapped with Platt calibration for reliable confidence scores.
    base_clf = LogisticRegression(max_iter=2000, random_state=42)
    clf = CalibratedClassifierCV(base_clf, cv=3, method="sigmoid")
    algorithm = "LogisticRegression+PlattCalibration"
    logger.info("Training LogisticRegression with Platt calibration ...")

    clf.fit(X_train_vec, y_train)

    y_pred = clf.predict(X_test_vec)
    acc = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    report_dict = classification_report(
        y_test, y_pred, target_names=le.classes_, output_dict=True, zero_division=0
    )
    report_str = classification_report(
        y_test, y_pred, target_names=le.classes_, zero_division=0
    )

    logger.info("\n%s", report_str)
    logger.info("Accuracy: %.4f (%.2f%%)  |  Macro F1: %.4f", acc, acc * 100, macro_f1)

    joblib.dump(clf, MODELS_DIR / "transaction_model.pkl")
    joblib.dump(vectorizer, MODELS_DIR / "vectorizer.pkl")
    joblib.dump(le, MODELS_DIR / "label_encoder.pkl")
    logger.info("Model artifacts saved to: %s", MODELS_DIR)

    training_report = {
        "algorithm": algorithm,
        "model_version": "v2",
        "accuracy": round(acc, 4),
        "macro_f1": round(macro_f1, 4),
        "split_type": split_type,
        "categories": list(le.classes_),
        "num_categories": int(len(le.classes_)),
        "num_training_samples": int(len(X_train)),
        "num_test_samples": int(len(X_test)),
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "dataset_path": str(dataset_path),
        "per_class_metrics": {
            cat: {
                "precision": round(float(report_dict[cat]["precision"]), 3),
                "recall": round(float(report_dict[cat]["recall"]), 3),
                "f1_score": round(float(report_dict[cat]["f1-score"]), 3),
                "support": int(report_dict[cat]["support"]),
            }
            for cat in le.classes_
            if cat in report_dict
        },
    }

    report_path = MODELS_DIR / "training_report.json"
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(training_report, fh, indent=2)
    logger.info("Training report saved to: %s", report_path)

    return training_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train TF-IDF + XGBoost transaction categorization model."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DATA_DIR / "transactions_train_v2.csv",
        help="Path to training CSV (columns: merchant_name, category[, brand]). "
        f"Default: {DATA_DIR / 'transactions_train_v2.csv'}",
    )
    args = parser.parse_args()

    if not args.dataset.exists():
        logger.error("Dataset not found: %s", args.dataset)
        logger.error("Expected CSV with columns: merchant_name, category")
        sys.exit(1)

    report = train(args.dataset)

    print(f"\n{'='*55}")
    print(f"  Algorithm  : {report['algorithm']}")
    print(f"  Accuracy   : {report['accuracy'] * 100:.2f}%  (split: {report['split_type']})")
    print(f"  Macro F1   : {report['macro_f1']:.4f}")
    print(f"  Categories : {report['num_categories']}")
    print(f"  Train size : {report['num_training_samples']}")
    print(f"  Test size  : {report['num_test_samples']}")
    print(f"{'='*55}")
    print(f"\nModel saved to: {MODELS_DIR}")
    print("Restart the backend server to load the new model.")
