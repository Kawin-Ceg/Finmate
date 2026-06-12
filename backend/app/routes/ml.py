from fastapi import APIRouter

from app.services.ml_categorizer import get_model_info, is_loaded

router = APIRouter(prefix="/ml", tags=["ML"])


@router.get("/model-info")
def get_ml_model_info():
    """Returns current ML model status, algorithm, and accuracy metrics."""
    if not is_loaded():
        return {
            "status": "not_loaded",
            "message": (
                "No trained model found. Run scripts/train_transaction_classifier.py "
                "to train the model, then restart the server."
            ),
        }

    info = get_model_info() or {}
    return {
        "status": "loaded",
        "algorithm": info.get("algorithm"),
        "accuracy": info.get("accuracy"),
        "num_categories": info.get("num_categories"),
        "categories": info.get("categories", []),
        "num_training_samples": info.get("num_training_samples"),
        "trained_at": info.get("trained_at"),
        "per_class_metrics": info.get("per_class_metrics", {}),
    }
