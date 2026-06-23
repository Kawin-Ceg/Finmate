"""
ML-based transaction category predictor.
Loads a trained TF-IDF + XGBoost model at startup.
Falls back gracefully when model files are absent.
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional

import joblib

logger = logging.getLogger(__name__)

_MODELS_DIR = Path(__file__).parent.parent.parent / "models"

_model = None
_vectorizer = None
_label_encoder = None
_model_info: Optional[dict] = None

CONFIDENCE_THRESHOLD = 0.50

# Strip common bank-statement prefixes before inference
_PREFIX_RE = re.compile(
    r"^(upi[-/\s]?|neft[-/\s]?|imps[-/\s]?|nach[-/\s]?|ecs[-/\s]?|"
    r"rtgs[-/\s]?|pos[-/\s]?|aeps[-/\s]?|ach[-/\s]?|cdm[-/\s]?|atm[-/\s]?)",
    re.IGNORECASE,
)
_NUMBER_RE = re.compile(r"\b\d{5,}\b")
_NON_ALPHA_RE = re.compile(r"[^a-z\s]")
_WHITESPACE_RE = re.compile(r"\s+")


def _clean(text: str) -> str:
    text = str(text).lower().strip()
    text = _PREFIX_RE.sub("", text)
    text = _NUMBER_RE.sub("", text)
    text = _NON_ALPHA_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def load_model() -> bool:
    """Load persisted model artifacts. Returns True if successful."""
    global _model, _vectorizer, _label_encoder, _model_info

    model_path = _MODELS_DIR / "transaction_model.pkl"
    vectorizer_path = _MODELS_DIR / "vectorizer.pkl"
    encoder_path = _MODELS_DIR / "label_encoder.pkl"

    if not all(p.exists() for p in (model_path, vectorizer_path, encoder_path)):
        logger.warning(
            "ML model files not found in %s — rule-based categorization active.",
            _MODELS_DIR,
        )
        return False

    try:
        _model = joblib.load(model_path)
        _vectorizer = joblib.load(vectorizer_path)
        _label_encoder = joblib.load(encoder_path)

        report_path = _MODELS_DIR / "training_report.json"
        if report_path.exists():
            with open(report_path, encoding="utf-8") as fh:
                _model_info = json.load(fh)

        algo = _model_info.get("algorithm", "unknown") if _model_info else "unknown"
        acc = _model_info.get("accuracy", 0) if _model_info else 0
        logger.info(
            "ML classifier loaded: %s | accuracy=%.2f%%", algo, acc * 100
        )
        return True

    except Exception as exc:
        logger.error("Failed to load ML model: %s", exc)
        _model = _vectorizer = _label_encoder = None
        return False


def predict_category(merchant: str, description: str = "") -> Optional[dict]:
    """
    Predict category for a transaction merchant string.

    Returns {"category": str, "confidence": float} or None if unavailable.
    """
    if _model is None:
        return None

    try:
        text = _clean(f"{merchant} {description}")
        X = _vectorizer.transform([text])
        proba = _model.predict_proba(X)[0]
        idx = int(proba.argmax())
        return {
            "category": str(_label_encoder.inverse_transform([idx])[0]),
            "confidence": float(proba[idx]),
        }
    except Exception as exc:
        logger.error("ML prediction error: %s", exc)
        return None


def is_loaded() -> bool:
    return _model is not None


def get_model_info() -> Optional[dict]:
    return _model_info
