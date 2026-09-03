import json
from pathlib import Path

from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/api/models",
    tags=["models"],
)


ARTIFACTS_DIR = (
    Path(__file__).resolve().parents[1]
    / "ml"
    / "artifacts"
)


@router.get("/production")
def get_production_model():
    metadata_path = (
        ARTIFACTS_DIR
        / "index_improvement_model_v2_final_metadata.json"
    )

    model_path = (
        ARTIFACTS_DIR
        / "index_improvement_model_v2_final.joblib"
    )

    if not metadata_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Production model metadata not found.",
        )

    with metadata_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        metadata = json.load(file)

    return {
        "status": "active",
        "model": {
            "version": (
                metadata.get("version")
                or metadata.get("model_version")
                or "v2-final"
            ),
            "feature_schema": (
                metadata.get("feature_schema")
                or "v2"
            ),
            "feature_count": len(
                metadata.get(
                    "features",
                    metadata.get(
                        "feature_names",
                        [],
                    ),
                )
            ),
            "features": metadata.get(
                "features",
                metadata.get(
                    "feature_names",
                    [],
                ),
            ),
            "training_samples": metadata.get(
                "samples",
                metadata.get(
                    "training_samples",
                ),
            ),
            "query_groups": metadata.get(
                "groups",
                metadata.get(
                    "query_groups",
                ),
            ),
            "artifact_exists": model_path.exists(),
            "artifact_name": model_path.name,
            "metadata_name": metadata_path.name,
        },
        "metadata": metadata,
    }