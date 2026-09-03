from __future__ import annotations

from app.ml.v2_feature_extractor import (
    build_v2_features,
)


def main() -> None:
    query = """
    SELECT *
    FROM orders
    WHERE customer_id = 50000
      AND status = 'PAID'
    ORDER BY created_at DESC
    """

    explain_result = {
        "plan": {
            "Node Type": "Gather",
            "Total Cost": 15997.22,
            "Plan Rows": 2,
            "Plans": [
                {
                    "Node Type": "Seq Scan",
                    "Relation Name": "orders",
                    "Actual Rows": 1,
                    "Actual Loops": 3,
                    "Actual Total Time": 32.875,
                    "Rows Removed by Filter": 333332,
                }
            ],
        }
    }

    recommendation = {
        "type": "INDEX",
        "table": "orders",
        "columns": [
            "customer_id",
            "status",
            "created_at",
        ],
        "reason": (
            "Seq Scan detected on public.orders. "
            "Filter columns: "
            "['customer_id', 'status']. "
            "Order column: created_at."
        ),
        "source": {
            "actual_rows": 1,
            "rows_removed_by_filter": 333332,
        },
    }

    features = build_v2_features(
        query=query,
        explain_result=explain_result,
        recommendation=recommendation,
    )

    print(
        "=" * 70
    )

    print(
        "DBOPTIMA V2 FEATURE TEST"
    )

    print(
        "=" * 70
    )

    for key, value in features.items():
        print(
            f"{key:35} = {value}"
        )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()