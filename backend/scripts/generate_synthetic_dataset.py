#!/usr/bin/env python
"""
Synthetic Transaction Dataset Generator — FinMate ML Upgrade Phase 2

Expands the original 889-row hand-curated dataset (kept 100% intact as the
"real" component) with rule-based synthetic merchant narrations built from
real Indian merchant brand names and realistic bank-statement formatting
patterns (UPI/NEFT/IMPS/POS prefixes, reference numbers, UPI handles,
casing variation, truncation).

This is NOT scraped or sourced from any real transaction log — every row is
generated from a template + brand-name combination. It is explicitly
documented as synthetic-majority data (see DATASET_REPORT.md) because no
real, labeled, Indian-merchant transaction-category dataset is available
through any source this script can access (see ML_AUDIT_REPORT.md, Section 4).

Usage:
    python scripts/generate_synthetic_dataset.py
"""
from __future__ import annotations

import csv
import random
import re
from collections import Counter
from pathlib import Path

random.seed(42)

SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
REAL_CSV = DATA_DIR / "transactions_train.csv"
OUTPUT_CSV = DATA_DIR / "transactions_train_v2.csv"

CANONICAL_CATEGORIES = {
    "Food", "Transport", "Shopping", "Utilities", "Health", "Insurance",
    "Investment", "Income", "Education", "Rent", "Entertainment",
    "Subscriptions", "Transfers", "Cash", "Other",
}

# ---------------------------------------------------------------------------
# Merchant brand banks — real, publicly known Indian (and a few global-in-India)
# brands per category. Deliberately broad to avoid the model overfitting to a
# handful of repeated names.
# ---------------------------------------------------------------------------

MERCHANTS: dict[str, list[str]] = {
    "Food": [
        "SWIGGY", "ZOMATO", "DOMINOS PIZZA", "KFC", "MCDONALDS", "PIZZA HUT",
        "SUBWAY", "STARBUCKS", "CAFE COFFEE DAY", "BURGER KING",
        "BEHROUZ BIRYANI", "FAASOS", "BOX8", "HALDIRAMS", "BARBEQUE NATION",
        "WOW MOMO", "CHAAYOS", "THEOBROMA", "BASKIN ROBBINS",
        "NATURALS ICE CREAM", "EATFIT", "FRESHMENU", "SWIGGY INSTAMART",
        "ZOMATO HYPERPURE", "MOJO PIZZA", "BIRYANI BLUES",
    ],
    "Transport": [
        "UBER", "OLA", "RAPIDO", "IRCTC", "INDIAN RAILWAYS", "DELHI METRO",
        "NAMMA METRO", "BMTC", "MUMBAI METRO", "REDBUS", "INDIGO AIRLINES",
        "SPICEJET", "AIR INDIA", "VISTARA", "HP PETROL PUMP", "INDIAN OIL",
        "BHARAT PETROLEUM", "FASTAG RECHARGE", "PARKING FEE", "OLA AUTO",
        "QUICK RIDE", "YULU BIKE", "BOUNCE SCOOTER",
    ],
    "Shopping": [
        "AMAZON", "FLIPKART", "MYNTRA", "AJIO", "NYKAA", "BIGBASKET",
        "ZEPTO", "BLINKIT", "MEESHO", "TATA CLIQ", "SNAPDEAL", "CROMA",
        "RELIANCE DIGITAL", "DECATHLON", "IKEA", "LIFESTYLE", "PANTALOONS",
        "SHOPPERS STOP", "WESTSIDE", "MAX FASHION", "FABINDIA",
    ],
    "Utilities": [
        "JIO", "AIRTEL", "VI VODAFONE IDEA", "BSNL", "BESCOM ELECTRICITY",
        "MSEB ELECTRICITY", "TATA POWER", "ADANI ELECTRICITY",
        "MAHANAGAR GAS", "INDANE GAS BOOKING", "HP GAS BOOKING",
        "WATER BOARD BILL", "ACT FIBERNET BROADBAND", "EXCITEL BROADBAND",
        "JIOFIBER", "TORRENT POWER",
    ],
    "Health": [
        "APOLLO PHARMACY", "PHARMEASY", "1MG", "NETMEDS", "PRACTO",
        "CULT FIT", "FITTERNITY", "MAX HOSPITAL", "FORTIS HOSPITAL",
        "APOLLO HOSPITAL", "MEDPLUS", "DR LAL PATHLABS", "THYROCARE",
        "GYM MEMBERSHIP FEE", "HEALTHIFYME", "MANIPAL HOSPITAL",
    ],
    "Insurance": [
        "LIC JEEVAN ANAND", "LIC PREMIUM PAYMENT", "LIC POLICY RENEWAL",
        "HDFC LIFE INSURANCE", "ICICI PRUDENTIAL LIFE", "STAR HEALTH INSURANCE",
        "MAX BUPA HEALTH INSURANCE", "BAJAJ ALLIANZ INSURANCE",
        "SBI LIFE INSURANCE", "TATA AIA LIFE", "NEW INDIA ASSURANCE",
        "RELIGARE HEALTH INSURANCE", "CARE HEALTH INSURANCE",
    ],
    "Investment": [
        "ZERODHA KITE", "GROWW", "UPSTOX", "PAYTM MONEY", "ICICI DIRECT",
        "HDFC SECURITIES", "ANGEL ONE", "MUTUAL FUND SIP", "NSDL DEPOSITORY",
        "CDSL DEPOSITORY", "COIN BY ZERODHA", "AXIS MUTUAL FUND",
        "SBI MUTUAL FUND", "KUVERA INVESTMENT",
    ],
    "Income": [
        "SALARY CREDIT", "PAYROLL CREDIT", "FREELANCE PAYMENT RECEIVED",
        "DIVIDEND CREDIT", "INTEREST CREDIT", "BONUS CREDIT",
        "REFUND CREDIT", "CASHBACK CREDIT", "CONSULTANCY FEE RECEIVED",
        "REIMBURSEMENT CREDIT",
    ],
    "Education": [
        "BYJUS", "UNACADEMY", "COURSERA", "UDEMY", "VEDANTU",
        "SCHOOL FEES PAYMENT", "COLLEGE FEES PAYMENT", "TUITION FEES",
        "NIIT", "AAKASH INSTITUTE", "FIITJEE", "PHYSICS WALLAH",
        "WHITEHAT JR",
    ],
    "Rent": [
        "HOUSE RENT PAYMENT", "PG RENT PAYMENT", "HOSTEL FEE PAYMENT",
        "LANDLORD PAYMENT", "FLAT RENT TRANSFER", "NESTAWAY RENT",
        "STANZA LIVING RENT", "ZOLO STAYS RENT",
    ],
    "Entertainment": [
        "BOOKMYSHOW", "PVR CINEMAS", "INOX MOVIES", "GAMING ZONE",
        "AMUSEMENT PARK TICKET", "CONCERT TICKET BOOKING",
        "STEAM GAMES PURCHASE", "PLAYSTATION STORE",
    ],
    "Subscriptions": [
        "NETFLIX", "SPOTIFY", "HOTSTAR", "JIOCINEMA", "AMAZON PRIME VIDEO",
        "YOUTUBE PREMIUM", "AUDIBLE", "ADOBE CREATIVE CLOUD",
        "MICROSOFT 365", "ICLOUD STORAGE", "GOOGLE ONE", "LINKEDIN PREMIUM",
        "GYM APP SUBSCRIPTION",
    ],
    "Transfers": [
        "NEFT TRANSFER", "IMPS TRANSFER", "UPI TRANSFER TO FRIEND",
        "RTGS TRANSFER", "FUND TRANSFER SELF ACCOUNT", "FAMILY TRANSFER",
        "RENT SPLIT TRANSFER",
    ],
    "Cash": [
        "ATM WITHDRAWAL HDFC", "ATM WITHDRAWAL SBI", "ATM WITHDRAWAL ICICI",
        "CASH WITHDRAWAL AXIS BANK", "CDM CASH DEPOSIT",
        "CASH WITHDRAWAL KOTAK",
    ],
    "Other": [
        "MISCELLANEOUS CHARGE", "BANK SERVICE CHARGE", "ATM FEE CHARGE",
        "SMS CHARGE", "ANNUAL MAINTENANCE CHARGE", "CHEQUE BOUNCE CHARGE",
        "GST CHARGE", "DONATION PAYMENT", "TEMPLE DONATION",
        "NGO DONATION",
    ],
}

# Target FINAL combined (real + synthetic) row count per category.
# Mild realistic imbalance preserved (Food/Shopping/Transport higher volume),
# every category guaranteed >=500 final rows for safe stratified CV later.
FINAL_TARGETS: dict[str, int] = {
    "Food": 1100, "Shopping": 950, "Transport": 900, "Utilities": 800,
    "Subscriptions": 700, "Entertainment": 750, "Health": 750,
    "Income": 650, "Transfers": 650, "Cash": 600, "Insurance": 600,
    "Investment": 650, "Education": 650, "Rent": 550, "Other": 550,
}

UPI_HANDLES = ["@ybl", "@paytm", "@oksbi", "@okhdfcbank", "@okicici", "@apl", "@axl"]
CITIES = ["BANGALORE", "MUMBAI", "DELHI", "PUNE", "HYDERABAD", "CHENNAI", "KOLKATA"]


def _ref() -> str:
    return str(random.randint(100000000, 999999999))


def _date_suffix() -> str:
    return f"{random.randint(1,28):02d}{random.choice(['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'])}"


TEMPLATES = [
    lambda m: f"UPI/{m}/{_ref()}",
    lambda m: f"UPI-{m}-{_ref()}{random.choice(UPI_HANDLES)}",
    lambda m: f"NEFT CR-{m}-{_ref()}",
    lambda m: f"NEFT DR-{m}",
    lambda m: f"IMPS/{_ref()}/{m}",
    lambda m: f"POS {m} {random.choice(CITIES)}",
    lambda m: f"POS/{m}/{_ref()}",
    lambda m: f"{m} ONLINE PAYMENT",
    lambda m: f"{m} PURCHASE {_ref()}",
    lambda m: f"ACH DR-{m}",
    lambda m: f"{m}",
    lambda m: f"{m} {_date_suffix()}",
    lambda m: f"BIL/{m}/{_ref()}",
    lambda m: f"{m}*{_ref()}",
    lambda m: f"{m} SI",
    lambda m: f"{m.title()}",
    lambda m: f"{m.lower()} payment",
]


def generate_for_category(category: str, count: int) -> list[tuple[str, str]]:
    """Returns (narration, source_brand) pairs. The source brand is tracked
    explicitly so that downstream model evaluation can hold out entire brands
    between train/test splits — a random row-level split would let 'SWIGGY'
    appear in both train and test (just with different template formatting),
    which measures formatting-robustness, not generalization to unseen
    merchants. See GROUP-AWARE SPLITTING note in DATASET_REPORT.md."""
    merchants = MERCHANTS[category]
    rows: dict[str, str] = {}  # narration -> brand
    attempts = 0
    max_attempts = count * 20
    while len(rows) < count and attempts < max_attempts:
        attempts += 1
        merchant = random.choice(merchants)
        template = random.choice(TEMPLATES)
        narration = template(merchant)
        rows[narration] = merchant
    return list(rows.items())


# Flat (brand, category) list sorted by descending brand length so longer,
# more specific brand names are matched before shorter substrings of them
# (e.g. "JIOCINEMA" before "JIO").
_ALL_BRANDS: list[tuple[str, str]] = sorted(
    ((brand, cat) for cat, brands in MERCHANTS.items() for brand in brands),
    key=lambda bc: -len(bc[0]),
)


def infer_brand(merchant_name: str) -> str:
    """Best-effort brand inference for real (v1) rows, which have no
    explicit brand label. Falls back to the cleaned merchant string itself
    as a singleton group if no known brand substring matches."""
    upper = merchant_name.upper()
    for brand, _cat in _ALL_BRANDS:
        if brand in upper:
            return brand
    return re.sub(r"[^A-Z]", "", upper) or upper


# ---------------------------------------------------------------------------
# Data quality pipeline
# ---------------------------------------------------------------------------

def load_real_rows() -> list[tuple[str, str, str]]:
    rows = []
    with open(REAL_CSV, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            merchant = row["merchant_name"]
            rows.append((merchant, row["category"], infer_brand(merchant)))
    return rows


def clean_and_validate(
    rows: list[tuple[str, str, str]]
) -> tuple[list[tuple[str, str, str]], dict]:
    """Apply the data quality pipeline: null handling, length-outlier removal,
    category validation, duplicate detection. Returns (clean_rows, stats)."""
    stats = {
        "input_count": len(rows),
        "null_or_empty_removed": 0,
        "length_outliers_removed": 0,
        "invalid_category_removed": 0,
        "exact_duplicates_removed": 0,
    }

    seen: set[tuple[str, str]] = set()
    clean: list[tuple[str, str, str]] = []

    for merchant, category, brand in rows:
        merchant = (merchant or "").strip()
        category = (category or "").strip()
        brand = (brand or "").strip()

        if not merchant or not category:
            stats["null_or_empty_removed"] += 1
            continue

        if category not in CANONICAL_CATEGORIES:
            stats["invalid_category_removed"] += 1
            continue

        cleaned_len = len(re.sub(r"[^A-Za-z]", "", merchant))
        if cleaned_len < 3 or len(merchant) > 200:
            stats["length_outliers_removed"] += 1
            continue

        key = (merchant.upper(), category)
        if key in seen:
            stats["exact_duplicates_removed"] += 1
            continue
        seen.add(key)
        clean.append((merchant, category, brand))

    stats["output_count"] = len(clean)
    return clean, stats


def main():
    real_rows = load_real_rows()
    real_count_by_cat = Counter(c for _, c, _ in real_rows)

    synthetic_rows: list[tuple[str, str, str]] = []
    synth_count_by_cat: dict[str, int] = {}

    for category, final_target in FINAL_TARGETS.items():
        existing = real_count_by_cat.get(category, 0)
        needed = max(0, final_target - existing)
        generated = generate_for_category(category, needed)
        synth_count_by_cat[category] = len(generated)
        synthetic_rows.extend((narration, category, brand) for narration, brand in generated)

    combined = real_rows + synthetic_rows
    clean_rows, quality_stats = clean_and_validate(combined)

    # Shuffle so real/synthetic rows aren't grouped (avoids any ordering bias
    # during train/test split, though stratify=True downstream makes this
    # largely moot — cheap insurance regardless).
    random.shuffle(clean_rows)

    DATA_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["merchant_name", "category", "brand"])
        writer.writerows(clean_rows)

    final_by_cat = Counter(c for _, c, _ in clean_rows)
    distinct_brands = len({b for _, _, b in clean_rows})

    print(f"Real rows loaded:       {len(real_rows)}")
    print(f"Synthetic rows generated: {len(synthetic_rows)}")
    print(f"Combined (pre-quality):  {len(combined)}")
    print(f"Quality pipeline stats:  {quality_stats}")
    print(f"Final dataset size:      {len(clean_rows)}")
    print(f"Distinct brand groups:   {distinct_brands}")
    print(f"Real-data ratio:         {len(real_rows) / len(clean_rows) * 100:.1f}%")
    print(f"\nFinal per-category distribution:")
    for cat in sorted(final_by_cat, key=lambda c: -final_by_cat[c]):
        real_n = real_count_by_cat.get(cat, 0)
        synth_n = synth_count_by_cat.get(cat, 0)
        print(f"  {cat:15s} {final_by_cat[cat]:5d}  (real={real_n}, synthetic={synth_n})")
    print(f"\nSaved to: {OUTPUT_CSV}")

    return {
        "real_count": len(real_rows),
        "synthetic_count": len(synthetic_rows),
        "combined_pre_quality": len(combined),
        "quality_stats": quality_stats,
        "final_count": len(clean_rows),
        "real_ratio_pct": round(len(real_rows) / len(clean_rows) * 100, 1),
        "real_count_by_cat": dict(real_count_by_cat),
        "synth_count_by_cat": synth_count_by_cat,
        "final_by_cat": dict(final_by_cat),
    }


if __name__ == "__main__":
    main()
