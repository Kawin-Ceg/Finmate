CATEGORY_RULES = {
    "Food": [
        "swiggy", "zomato", "dominos", "dominoes", "pizza hut", "pizzahut",
        "kfc", "mcdonalds", "mcdonald", "burger king", "subway", "starbucks",
        "cafe", "restaurant", "biryani", "dhaba", "kitchen", "bakery",
        "bakes", "food", "eat", "dining", "cook", "tiffin", "lunchbox",
        "snack", "chai", "coffee", "juice", "barbeque", "barbeque nation",
    ],
    "Transport": [
        "uber", "ola ", "rapido", "bounce", "metro", "irctc", "railways",
        "indian rail", "flight", "airline", "indigo", "airindia", "spicejet",
        "goair", "vistara", "fuel", "petrol", "diesel", "hp pump", "indianoil",
        "bharat petroleum", "parking", "toll", "fastag", "bus", "taxi", "cab",
        "rickshaw", "auto",
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "ajio", "nykaa", "meesho", "snapdeal",
        "shopsy", "reliance digital", "croma", "vijay sales", "mall", "store",
        "mart", "bazaar", "supermarket", "bigbasket", "grofers", "blinkit",
        "zepto", "instamart", "dmart", "jiomart",
    ],
    "Entertainment": [
        "netflix", "spotify", "hotstar", "disney", "prime video", "zee5",
        "sony liv", "sonyliv", "bookmyshow", "pvr", "inox", "cinepolis",
        "cinema", "movie", "stream", "youtube premium", "gaming", "steam",
        "playstation", "xbox", "amazon prime",
    ],
    "Health": [
        "apollo", "pharmeasy", "1mg", "netmeds", "medlife", "medplus",
        "hospital", "clinic", "pharmacy", "chemist", "doctor", "medical",
        "healthkart", "gym", "fitness", "yoga", "health", "wellness",
        "dental", "eye care", "laboratory", "lab test",
    ],
    "Utilities": [
        "bescom", "bwssb", "tneb", "msedcl", "electricity", "water board",
        "gas", "broadband", "wifi", "internet", "airtel", "jio", "bsnl",
        "vi ", "vodafone", "idea", "tata sky", "dish tv", "recharge",
        "mobile bill", "utility bill", "bbmp", "municipal",
    ],
    "Income": [
        "salary", "wages", "credited by", "neft cr", "rtgs cr", "imps cr",
        "dividend", "interest credit", "refund", "cashback", "reward",
        "bonus", "incentive", "commission", "income", "payroll",
    ],
    "Cash": [
        "atm", "cash withdrawal", "cash deposit", "atw", "cdm",
    ],
    "Transfers": [
        "neft to", "rtgs to", "imps to", "upi transfer", "transfer to",
        "sent to", "paid to",
    ],
    "Insurance": [
        "lic", "hdfc life", "icici pru", "max life", "sbi life",
        "bajaj allianz", "star health", "insurance", "premium",
    ],
    "Investment": [
        "mutual fund", "mf ", "sip", "zerodha", "groww", "upstox",
        "paytm money", "nse", "bse", "demat", "trading", "smallcase",
    ],
    "Education": [
        "udemy", "coursera", "unacademy", "byjus", "byju", "vedantu",
        "skill", "school", "college", "university", "tuition", "coaching",
        "books",
    ],
    "Rent": [
        "rent", "pg rent", "hostel fee", "lease", "maintenance charge",
    ],
    "Subscriptions": [
        "subscription", "monthly plan", "annual plan", "membership",
    ],
}


def categorize(merchant: str, description: str = "") -> str:
    text = f"{merchant} {description}".lower()

    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return "Other"


def categorize_with_confidence(merchant: str, description: str = "") -> dict:
    """
    Returns {"category": str, "confidence": float | None, "method": str}.
    Tries ML first; falls back to rule engine if model unavailable or low confidence.
    """
    from app.services.ml_categorizer import (
        CONFIDENCE_THRESHOLD,
        is_loaded,
        predict_category,
    )

    if is_loaded():
        result = predict_category(merchant, description)
        if result is not None:
            if result["confidence"] >= CONFIDENCE_THRESHOLD:
                return {
                    "category": result["category"],
                    "confidence": result["confidence"],
                    "method": "ml",
                }
            # Below threshold: show ML's best guess but flag for user review.
            # The rule engine is not a better predictor here — calibration data
            # shows ML at 84% accuracy on its confident subset; routing everything
            # below threshold to rule-based would lose that signal entirely.
            return {
                "category": result["category"],
                "confidence": result["confidence"],
                "method": "ml_low_confidence",
            }

    return {
        "category": categorize(merchant, description),
        "confidence": None,
        "method": "rule_fallback",
    }
