from __future__ import annotations

import re
from typing import Any


EQUALITY_PATTERN = re.compile(
    r"(?<![<>!=])=(?!=)",
    re.IGNORECASE,
)

RANGE_PATTERN = re.compile(
    r"(>=|<=|<>|!=|>|<|\bBETWEEN\b)",
    re.IGNORECASE,
)

LIKE_PATTERN = re.compile(
    r"\b(?:LIKE|ILIKE)\b",
    re.IGNORECASE,
)

ORDER_BY_PATTERN = re.compile(
    r"\bORDER\s+BY\b",
    re.IGNORECASE,
)

LIMIT_PATTERN = re.compile(
    r"\bLIMIT\s+\d+\b",
    re.IGNORECASE,
)


def _to_float(
    value: Any,
) -> float | None:
    if value is None:
        return None

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return None


def _to_int(
    value: Any,
) -> int | None:
    if value is None:
        return None

    try:
        return int(value)

    except (
        TypeError,
        ValueError,
    ):
        return None


def walk_plan_nodes(
    node: dict[str, Any],
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []

    if not isinstance(
        node,
        dict,
    ):
        return nodes

    nodes.append(
        node
    )

    children = (
        node.get(
            "Plans"
        )
        or []
    )

    for child in children:
        if isinstance(
            child,
            dict,
        ):
            nodes.extend(
                walk_plan_nodes(
                    child
                )
            )

    return nodes


def extract_plan_root(
    explain_result: dict[str, Any],
) -> dict[str, Any]:
    plan = explain_result.get(
        "plan"
    )

    if isinstance(
        plan,
        dict,
    ):
        nested = plan.get(
            "Plan"
        )

        if isinstance(
            nested,
            dict,
        ):
            return nested

        return plan

    plan_json = explain_result.get(
        "plan_json"
    )

    if (
        isinstance(
            plan_json,
            list,
        )
        and plan_json
        and isinstance(
            plan_json[0],
            dict,
        )
    ):
        first = plan_json[0]

        nested = first.get(
            "Plan"
        )

        if isinstance(
            nested,
            dict,
        ):
            return nested

        return first

    return {}


def extract_plan_v2_features(
    explain_result: dict[str, Any],
) -> dict[str, Any]:
    root = extract_plan_root(
        explain_result
    )

    nodes = walk_plan_nodes(
        root
    )

    seq_scan_nodes = [
        node
        for node in nodes
        if node.get(
            "Node Type"
        )
        == "Seq Scan"
    ]

    rows_removed = sum(
        float(
            node.get(
                "Rows Removed by Filter"
            )
            or 0.0
        )
        for node in seq_scan_nodes
    )

    actual_rows = sum(
        float(
            node.get(
                "Actual Rows"
            )
            or 0.0
        )
        for node in seq_scan_nodes
    )

    actual_total_time = sum(
        float(
            node.get(
                "Actual Total Time"
            )
            or 0.0
        )
        for node in seq_scan_nodes
    )

    actual_loops = sum(
        float(
            node.get(
                "Actual Loops"
            )
            or 0.0
        )
        for node in seq_scan_nodes
    )

    scanned_rows_estimate = (
        rows_removed
        + actual_rows
    )

    selectivity_ratio = None

    if scanned_rows_estimate > 0:
        selectivity_ratio = (
            actual_rows
            / scanned_rows_estimate
        )

    removed_to_returned_ratio = None

    if actual_rows > 0:
        removed_to_returned_ratio = (
            rows_removed
            / actual_rows
        )

    return {
        "seq_scan_count": len(
            seq_scan_nodes
        ),
        "actual_rows": round(
            actual_rows,
            4,
        ),
        "rows_removed_by_filter": round(
            rows_removed,
            4,
        ),
        "actual_total_time_ms": round(
            actual_total_time,
            4,
        ),
        "actual_loops": round(
            actual_loops,
            4,
        ),
        "scan_selectivity_ratio": (
            round(
                selectivity_ratio,
                8,
            )
            if selectivity_ratio
            is not None
            else None
        ),
        "removed_to_returned_ratio": (
            round(
                removed_to_returned_ratio,
                4,
            )
            if removed_to_returned_ratio
            is not None
            else None
        ),
    }


def extract_query_v2_features(
    query: str,
) -> dict[str, Any]:
    normalized_query = (
        " ".join(
            query.strip().split()
        )
    )

    equality_filter_count = len(
        EQUALITY_PATTERN.findall(
            normalized_query
        )
    )

    range_filter_count = len(
        RANGE_PATTERN.findall(
            normalized_query
        )
    )

    like_filter_count = len(
        LIKE_PATTERN.findall(
            normalized_query
        )
    )

    has_order_by = bool(
        ORDER_BY_PATTERN.search(
            normalized_query
        )
    )

    has_limit = bool(
        LIMIT_PATTERN.search(
            normalized_query
        )
    )

    return {
        "equality_filter_count": (
            equality_filter_count
        ),
        "range_filter_count": (
            range_filter_count
        ),
        "like_filter_count": (
            like_filter_count
        ),
        "has_order_by": int(
            has_order_by
        ),
        "has_limit": int(
            has_limit
        ),
    }


def extract_candidate_v2_features(
    recommendation: dict[str, Any],
) -> dict[str, Any]:
    columns = (
        recommendation.get(
            "columns"
        )
        or []
    )

    source = (
        recommendation.get(
            "source"
        )
        or {}
    )

    reason = str(
        recommendation.get(
            "reason"
        )
        or ""
    )

    has_order_column = (
        "Order column:"
        in reason
    )

    source_actual_rows = (
        _to_float(
            source.get(
                "actual_rows"
            )
        )
    )

    source_rows_removed = (
        _to_float(
            source.get(
                "rows_removed_by_filter"
            )
        )
    )

    return {
        "candidate_column_count_v2": (
            len(
                columns
            )
        ),
        "candidate_has_order_column": int(
            has_order_column
        ),
        "source_actual_rows": (
            source_actual_rows
        ),
        "source_rows_removed_by_filter": (
            source_rows_removed
        ),
    }


def build_v2_features(
    query: str,
    explain_result: dict[str, Any],
    recommendation: dict[str, Any],
) -> dict[str, Any]:
    features: dict[
        str,
        Any,
    ] = {}

    features.update(
        extract_plan_v2_features(
            explain_result
        )
    )

    features.update(
        extract_query_v2_features(
            query
        )
    )

    features.update(
        extract_candidate_v2_features(
            recommendation
        )
    )

    return features