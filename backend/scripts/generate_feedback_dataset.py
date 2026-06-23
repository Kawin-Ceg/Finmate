#!/usr/bin/env python
"""
Feedback Dataset Generator — FinMate ML Upgrade Phase 6

Reads user corrections from the `category_feedback` table and merges them
with the base training dataset to produce an updated training CSV.

Correction rows are WEIGHTED: each correction is duplicated `weight` times
so the model treats them as stronger signal than synthetic rows. This is
intentional — a real user explicitly correcting a real transaction is the
highest-quality label in the system.

Usage:
    python scripts/generate_feedback_dataset.py [--weight 5] [--out data/transactions_retrain.csv]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

BASE_DATASET = BACKEND_DIR / "data" / "transactions_train_v2.csv"
DEFAULT_OUT = BACKEND_DIR / "data" / "transactions_retrain.csv"
DEFAULT_WEIGHT = 5


def main():
    parser = argparse.ArgumentParser(description="Generate feedback-augmented training dataset")
    parser.add_argument("--weight", type=int, default=DEFAULT_WEIGHT,
                        help=f"How many times to duplicate each correction row (default: {DEFAULT_WEIGHT})")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help=f"Output CSV path (default: {DEFAULT_OUT})")
    parser.add_argument("--database-url", type=str,
                        default=os.getenv("DATABASE_URL"),
                        help="Postgres URL (default: $DATABASE_URL)")
    args = parser.parse_args()

    if not args.database_url:
        print("ERROR: DATABASE_URL not set. Pass --database-url or export DATABASE_URL.")
        sys.exit(1)

    import pandas as pd
    from sqlalchemy import create_engine, text

    engine = create_engine(args.database_url)

    # Load base synthetic dataset
    base_df = pd.read_csv(BASE_DATASET)
    print(f"Base dataset: {len(base_df)} rows")

    # Load corrections from DB
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT merchant_name, corrected_category FROM category_feedback"
        )).fetchall()

    if not rows:
        print("No feedback corrections found in DB. Output will be the base dataset unchanged.")
        base_df.to_csv(args.out, index=False)
        print(f"Written to {args.out}")
        return

    corrections_df = pd.DataFrame(rows, columns=["merchant_name", "category"])
    # Assign synthetic brand = merchant_name (singleton group — won't leak across CV splits)
    corrections_df["brand"] = corrections_df["merchant_name"]
    print(f"Corrections: {len(corrections_df)} rows from {corrections_df['merchant_name'].nunique()} unique merchants")

    # Duplicate corrections by weight
    weighted = pd.concat([corrections_df] * args.weight, ignore_index=True)
    print(f"After weighting (x{args.weight}): {len(weighted)} correction rows")

    # Merge
    combined = pd.concat([base_df, weighted], ignore_index=True)
    combined.to_csv(args.out, index=False)
    print(f"Combined dataset: {len(combined)} rows → {args.out}")


if __name__ == "__main__":
    main()
