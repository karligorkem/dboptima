from fastapi import APIRouter

from app.core.config import get_settings


router = APIRouter(
    prefix="/api/settings",
    tags=["settings"],
)


@router.get("")
def get_application_settings():
    settings = get_settings()

    return {
        "application": {
            "name": settings.app_name,
            "environment": settings.app_env,
        },
        "recommendation_policy": {
            "recommended_threshold_percent": 20,
            "review_threshold_percent": 5,
            "rejected_below_percent": 5,
        },
        "benchmark_policy": {
            "warmup_runs": 1,
            "measurement_runs": 5,
            "decision_metric": "median",
            "temporary_index": True,
            "keep_index_after_benchmark": False,
        },
        "safety": {
            "explain_analyze_executes_query": True,
            "automatic_index_application": False,
            "benchmark_is_final_authority": True,
            "ml_ranking_enabled": True,
        },
        "model": {
            "production_version": "v2-final",
            "feature_schema": "v2",
            "feature_count": 26,
        },
    }