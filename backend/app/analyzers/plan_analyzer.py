from typing import Any


def find_sequential_scans(
    plan: dict[str, Any],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    def walk(node: dict[str, Any]) -> None:
        node_type = node.get("Node Type")

        if node_type in {
            "Seq Scan",
            "Parallel Seq Scan",
        }:
            findings.append(
                {
                    "node_type": node_type,
                    "relation_name": node.get("Relation Name"),
                    "schema": node.get("Schema"),
                    "alias": node.get("Alias"),
                    "filter": node.get("Filter"),
                    "plan_rows": node.get("Plan Rows"),
                    "actual_rows": node.get("Actual Rows"),
                    "actual_loops": node.get("Actual Loops"),
                    "startup_cost": node.get("Startup Cost"),
                    "total_cost": node.get("Total Cost"),
                    "actual_startup_time": node.get(
                        "Actual Startup Time"
                    ),
                    "actual_total_time": node.get(
                        "Actual Total Time"
                    ),
                    "rows_removed_by_filter": node.get(
                        "Rows Removed by Filter"
                    ),
                }
            )

        child_plans = node.get("Plans", [])

        for child in child_plans:
            walk(child)

    walk(plan)

    return findings