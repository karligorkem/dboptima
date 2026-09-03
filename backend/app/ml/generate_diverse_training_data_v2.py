from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable


API_BASE_URL = "http://127.0.0.1:8000"
DATABASE_ID = 2

RUNS_PER_FAMILY = 6
REQUEST_TIMEOUT_SECONDS = 180
SLEEP_BETWEEN_REQUESTS = 0.10

random.seed(42)


# ============================================================
# FAMILY DEFINITION
# ============================================================


@dataclass
class QueryFamily:
    name: str
    builder: Callable[[int], str]


# ============================================================
# TEST VALUES
# ============================================================


CUSTOMER_IDS = [
    1111,
    5000,
    10000,
    25000,
    50000,
    75000,
]

ORDER_IDS = [
    1000,
    5000,
    12000,
    30000,
    54321,
    85000,
]

PRODUCT_IDS = [
    100,
    1000,
    5000,
    12345,
    20000,
    40000,
]

STATUSES = [
    "PAID",
    "PENDING",
    "SHIPPED",
    "PAID",
    "PENDING",
    "SHIPPED",
]

AMOUNT_LOW = [
    25,
    100,
    250,
    500,
    750,
    1200,
]

AMOUNT_HIGH = [
    75,
    250,
    500,
    900,
    1400,
    2000,
]

PRICE_LOW = [
    5,
    20,
    50,
    100,
    250,
    500,
]

PRICE_HIGH = [
    25,
    75,
    150,
    300,
    600,
    1200,
]

DATES = [
    "2024-01-01",
    "2024-06-01",
    "2025-01-01",
    "2025-03-01",
    "2025-06-01",
    "2025-09-01",
]

DATE_ENDS = [
    "2024-02-01",
    "2024-07-01",
    "2025-02-01",
    "2025-04-01",
    "2025-07-01",
    "2025-10-01",
]

LIMITS = [
    5,
    10,
    25,
    50,
    100,
    250,
]


# ============================================================
# SQL UTIL
# ============================================================


def normalize_sql(query: str) -> str:
    return " ".join(
        query.strip().split()
    )


# ============================================================
# ORDERS FAMILIES
# ============================================================


def orders_customer_eq(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE customer_id = {CUSTOMER_IDS[i]};
    """


def orders_customer_eq_order_created(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE customer_id = {CUSTOMER_IDS[i]}
    ORDER BY created_at DESC;
    """


def orders_customer_eq_limit(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE customer_id = {CUSTOMER_IDS[i]}
    LIMIT {LIMITS[i]};
    """


def orders_customer_eq_order_limit(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE customer_id = {CUSTOMER_IDS[i]}
    ORDER BY created_at DESC
    LIMIT {LIMITS[i]};
    """


def orders_status_eq(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE status = '{STATUSES[i]}';
    """


def orders_status_order_created(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE status = '{STATUSES[i]}'
    ORDER BY created_at DESC;
    """


def orders_status_order_created_limit(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE status = '{STATUSES[i]}'
    ORDER BY created_at DESC
    LIMIT {LIMITS[i]};
    """


def orders_amount_gt(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE total_amount > {AMOUNT_LOW[i]};
    """


def orders_amount_lt(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE total_amount < {AMOUNT_HIGH[i]};
    """


def orders_amount_between(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE total_amount
    BETWEEN {AMOUNT_LOW[i]} AND {AMOUNT_HIGH[i]};
    """


def orders_amount_gt_order(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE total_amount > {AMOUNT_LOW[i]}
    ORDER BY total_amount DESC;
    """


def orders_amount_between_order(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE total_amount
    BETWEEN {AMOUNT_LOW[i]} AND {AMOUNT_HIGH[i]}
    ORDER BY total_amount DESC;
    """


def orders_customer_status(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE customer_id = {CUSTOMER_IDS[i]}
      AND status = '{STATUSES[i]}';
    """


def orders_customer_status_order(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE customer_id = {CUSTOMER_IDS[i]}
      AND status = '{STATUSES[i]}'
    ORDER BY created_at DESC;
    """


def orders_customer_status_limit(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE customer_id = {CUSTOMER_IDS[i]}
      AND status = '{STATUSES[i]}'
    LIMIT {LIMITS[i]};
    """


def orders_customer_amount_gt(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE customer_id = {CUSTOMER_IDS[i]}
      AND total_amount > {AMOUNT_LOW[i]};
    """


def orders_customer_amount_order(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE customer_id = {CUSTOMER_IDS[i]}
      AND total_amount > {AMOUNT_LOW[i]}
    ORDER BY total_amount DESC;
    """


def orders_status_amount_gt(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE status = '{STATUSES[i]}'
      AND total_amount > {AMOUNT_LOW[i]};
    """


def orders_status_amount_order(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE status = '{STATUSES[i]}'
      AND total_amount > {AMOUNT_LOW[i]}
    ORDER BY total_amount DESC;
    """


def orders_created_gt(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE created_at >= '{DATES[i]}';
    """


def orders_created_gt_order(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE created_at >= '{DATES[i]}'
    ORDER BY created_at DESC;
    """


def orders_created_between(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE created_at >= '{DATES[i]}'
      AND created_at < '{DATE_ENDS[i]}';
    """


def orders_created_between_order(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE created_at >= '{DATES[i]}'
      AND created_at < '{DATE_ENDS[i]}'
    ORDER BY created_at DESC;
    """


def orders_status_created(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE status = '{STATUSES[i]}'
      AND created_at >= '{DATES[i]}';
    """


def orders_status_created_order(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE status = '{STATUSES[i]}'
      AND created_at >= '{DATES[i]}'
    ORDER BY created_at DESC;
    """


def orders_customer_created(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE customer_id = {CUSTOMER_IDS[i]}
      AND created_at >= '{DATES[i]}';
    """


def orders_customer_created_order(i: int) -> str:
    return f"""
    SELECT *
    FROM orders
    WHERE customer_id = {CUSTOMER_IDS[i]}
      AND created_at >= '{DATES[i]}'
    ORDER BY created_at DESC;
    """


# ============================================================
# ORDER ITEMS FAMILIES
# ============================================================


def order_items_order_id(i: int) -> str:
    return f"""
    SELECT *
    FROM order_items
    WHERE order_id = {ORDER_IDS[i]};
    """


def order_items_order_id_order(i: int) -> str:
    return f"""
    SELECT *
    FROM order_items
    WHERE order_id = {ORDER_IDS[i]}
    ORDER BY id DESC;
    """


def order_items_order_id_limit(i: int) -> str:
    return f"""
    SELECT *
    FROM order_items
    WHERE order_id = {ORDER_IDS[i]}
    LIMIT {LIMITS[i]};
    """


def order_items_order_id_order_limit(i: int) -> str:
    return f"""
    SELECT *
    FROM order_items
    WHERE order_id = {ORDER_IDS[i]}
    ORDER BY id DESC
    LIMIT {LIMITS[i]};
    """


def order_items_product_id(i: int) -> str:
    return f"""
    SELECT *
    FROM order_items
    WHERE product_id = {PRODUCT_IDS[i]};
    """


def order_items_product_id_order(i: int) -> str:
    return f"""
    SELECT *
    FROM order_items
    WHERE product_id = {PRODUCT_IDS[i]}
    ORDER BY id DESC;
    """


def order_items_product_id_limit(i: int) -> str:
    return f"""
    SELECT *
    FROM order_items
    WHERE product_id = {PRODUCT_IDS[i]}
    LIMIT {LIMITS[i]};
    """


def order_items_product_id_order_limit(i: int) -> str:
    return f"""
    SELECT *
    FROM order_items
    WHERE product_id = {PRODUCT_IDS[i]}
    ORDER BY id DESC
    LIMIT {LIMITS[i]};
    """


def order_items_order_product(i: int) -> str:
    return f"""
    SELECT *
    FROM order_items
    WHERE order_id = {ORDER_IDS[i]}
      AND product_id = {PRODUCT_IDS[i]};
    """


def order_items_order_product_order(i: int) -> str:
    return f"""
    SELECT *
    FROM order_items
    WHERE order_id = {ORDER_IDS[i]}
      AND product_id = {PRODUCT_IDS[i]}
    ORDER BY id DESC;
    """


# ============================================================
# PRODUCTS FAMILIES
# ============================================================


def products_price_gt(i: int) -> str:
    return f"""
    SELECT *
    FROM products
    WHERE price > {PRICE_LOW[i]};
    """


def products_price_lt(i: int) -> str:
    return f"""
    SELECT *
    FROM products
    WHERE price < {PRICE_HIGH[i]};
    """


def products_price_between(i: int) -> str:
    return f"""
    SELECT *
    FROM products
    WHERE price
    BETWEEN {PRICE_LOW[i]} AND {PRICE_HIGH[i]};
    """


def products_price_gt_order(i: int) -> str:
    return f"""
    SELECT *
    FROM products
    WHERE price > {PRICE_LOW[i]}
    ORDER BY price DESC;
    """


def products_price_lt_order(i: int) -> str:
    return f"""
    SELECT *
    FROM products
    WHERE price < {PRICE_HIGH[i]}
    ORDER BY price ASC;
    """


def products_price_between_order(i: int) -> str:
    return f"""
    SELECT *
    FROM products
    WHERE price
    BETWEEN {PRICE_LOW[i]} AND {PRICE_HIGH[i]}
    ORDER BY price DESC;
    """


def products_price_gt_limit(i: int) -> str:
    return f"""
    SELECT *
    FROM products
    WHERE price > {PRICE_LOW[i]}
    LIMIT {LIMITS[i]};
    """


def products_price_gt_order_limit(i: int) -> str:
    return f"""
    SELECT *
    FROM products
    WHERE price > {PRICE_LOW[i]}
    ORDER BY price DESC
    LIMIT {LIMITS[i]};
    """


# ============================================================
# CUSTOMERS FAMILIES
# ============================================================


def customers_created_gt(i: int) -> str:
    return f"""
    SELECT *
    FROM customers
    WHERE created_at >= '{DATES[i]}';
    """


def customers_created_gt_order(i: int) -> str:
    return f"""
    SELECT *
    FROM customers
    WHERE created_at >= '{DATES[i]}'
    ORDER BY created_at DESC;
    """


def customers_created_between(i: int) -> str:
    return f"""
    SELECT *
    FROM customers
    WHERE created_at >= '{DATES[i]}'
      AND created_at < '{DATE_ENDS[i]}';
    """


def customers_created_between_order(i: int) -> str:
    return f"""
    SELECT *
    FROM customers
    WHERE created_at >= '{DATES[i]}'
      AND created_at < '{DATE_ENDS[i]}'
    ORDER BY created_at DESC;
    """


def customers_created_gt_limit(i: int) -> str:
    return f"""
    SELECT *
    FROM customers
    WHERE created_at >= '{DATES[i]}'
    LIMIT {LIMITS[i]};
    """


def customers_created_order_limit(i: int) -> str:
    return f"""
    SELECT *
    FROM customers
    WHERE created_at >= '{DATES[i]}'
    ORDER BY created_at DESC
    LIMIT {LIMITS[i]};
    """


# ============================================================
# FAMILY REGISTRY
# ============================================================


QUERY_FAMILIES: list[QueryFamily] = [

    # Orders - 28
    QueryFamily(
        "orders_customer_eq",
        orders_customer_eq,
    ),
    QueryFamily(
        "orders_customer_eq_order_created",
        orders_customer_eq_order_created,
    ),
    QueryFamily(
        "orders_customer_eq_limit",
        orders_customer_eq_limit,
    ),
    QueryFamily(
        "orders_customer_eq_order_limit",
        orders_customer_eq_order_limit,
    ),

    QueryFamily(
        "orders_status_eq",
        orders_status_eq,
    ),
    QueryFamily(
        "orders_status_order_created",
        orders_status_order_created,
    ),
    QueryFamily(
        "orders_status_order_created_limit",
        orders_status_order_created_limit,
    ),

    QueryFamily(
        "orders_amount_gt",
        orders_amount_gt,
    ),
    QueryFamily(
        "orders_amount_lt",
        orders_amount_lt,
    ),
    QueryFamily(
        "orders_amount_between",
        orders_amount_between,
    ),
    QueryFamily(
        "orders_amount_gt_order",
        orders_amount_gt_order,
    ),
    QueryFamily(
        "orders_amount_between_order",
        orders_amount_between_order,
    ),

    QueryFamily(
        "orders_customer_status",
        orders_customer_status,
    ),
    QueryFamily(
        "orders_customer_status_order",
        orders_customer_status_order,
    ),
    QueryFamily(
        "orders_customer_status_limit",
        orders_customer_status_limit,
    ),

    QueryFamily(
        "orders_customer_amount_gt",
        orders_customer_amount_gt,
    ),
    QueryFamily(
        "orders_customer_amount_order",
        orders_customer_amount_order,
    ),

    QueryFamily(
        "orders_status_amount_gt",
        orders_status_amount_gt,
    ),
    QueryFamily(
        "orders_status_amount_order",
        orders_status_amount_order,
    ),

    QueryFamily(
        "orders_created_gt",
        orders_created_gt,
    ),
    QueryFamily(
        "orders_created_gt_order",
        orders_created_gt_order,
    ),
    QueryFamily(
        "orders_created_between",
        orders_created_between,
    ),
    QueryFamily(
        "orders_created_between_order",
        orders_created_between_order,
    ),

    QueryFamily(
        "orders_status_created",
        orders_status_created,
    ),
    QueryFamily(
        "orders_status_created_order",
        orders_status_created_order,
    ),

    QueryFamily(
        "orders_customer_created",
        orders_customer_created,
    ),
    QueryFamily(
        "orders_customer_created_order",
        orders_customer_created_order,
    ),

    # Order items - 10
    QueryFamily(
        "order_items_order_id",
        order_items_order_id,
    ),
    QueryFamily(
        "order_items_order_id_order",
        order_items_order_id_order,
    ),
    QueryFamily(
        "order_items_order_id_limit",
        order_items_order_id_limit,
    ),
    QueryFamily(
        "order_items_order_id_order_limit",
        order_items_order_id_order_limit,
    ),

    QueryFamily(
        "order_items_product_id",
        order_items_product_id,
    ),
    QueryFamily(
        "order_items_product_id_order",
        order_items_product_id_order,
    ),
    QueryFamily(
        "order_items_product_id_limit",
        order_items_product_id_limit,
    ),
    QueryFamily(
        "order_items_product_id_order_limit",
        order_items_product_id_order_limit,
    ),

    QueryFamily(
        "order_items_order_product",
        order_items_order_product,
    ),
    QueryFamily(
        "order_items_order_product_order",
        order_items_order_product_order,
    ),

    # Products - 8
    QueryFamily(
        "products_price_gt",
        products_price_gt,
    ),
    QueryFamily(
        "products_price_lt",
        products_price_lt,
    ),
    QueryFamily(
        "products_price_between",
        products_price_between,
    ),
    QueryFamily(
        "products_price_gt_order",
        products_price_gt_order,
    ),
    QueryFamily(
        "products_price_lt_order",
        products_price_lt_order,
    ),
    QueryFamily(
        "products_price_between_order",
        products_price_between_order,
    ),
    QueryFamily(
        "products_price_gt_limit",
        products_price_gt_limit,
    ),
    QueryFamily(
        "products_price_gt_order_limit",
        products_price_gt_order_limit,
    ),

    # Customers - 6
    QueryFamily(
        "customers_created_gt",
        customers_created_gt,
    ),
    QueryFamily(
        "customers_created_gt_order",
        customers_created_gt_order,
    ),
    QueryFamily(
        "customers_created_between",
        customers_created_between,
    ),
    QueryFamily(
        "customers_created_between_order",
        customers_created_between_order,
    ),
    QueryFamily(
        "customers_created_gt_limit",
        customers_created_gt_limit,
    ),
    QueryFamily(
        "customers_created_order_limit",
        customers_created_order_limit,
    ),
]


# ============================================================
# API
# ============================================================


def optimize_query(
    query: str,
) -> dict:

    url = (
        f"{API_BASE_URL}"
        f"/api/databases/"
        f"{DATABASE_ID}"
        f"/optimize-query"
    )

    payload = json.dumps(
        {
            "query": normalize_sql(
                query
            )
        }
    ).encode(
        "utf-8"
    )

    request = urllib.request.Request(
        url=url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=REQUEST_TIMEOUT_SECONDS,
    ) as response:

        raw = response.read().decode(
            "utf-8"
        )

        return json.loads(
            raw
        )


# ============================================================
# RESULT PRINTING
# ============================================================


def print_result(
    family_name: str,
    run_number: int,
    response: dict,
) -> tuple[int, int]:

    candidate_count = int(
        response.get(
            "candidate_count",
            0,
        )
        or 0
    )

    persistence = (
        response.get(
            "persistence",
            {},
        )
        or {}
    )

    v2_ids = (
        persistence.get(
            "ml_training_sample_v2_ids",
            [],
        )
        or []
    )

    candidates = (
        response.get(
            "candidates",
            [],
        )
        or []
    )

    predicted = None
    actual = None
    status = None

    if candidates:

        first = candidates[0]

        prediction = (
            first.get(
                "ml_prediction",
                {},
            )
            or {}
        )

        benchmark = (
            first.get(
                "benchmark",
                {},
            )
            or {}
        )

        decision = (
            first.get(
                "decision",
                {},
            )
            or {}
        )

        predicted = prediction.get(
            "predicted_improvement_percent"
        )

        actual = benchmark.get(
            "improvement_percent"
        )

        status = decision.get(
            "status"
        )

    print(
        f"[OK] "
        f"{family_name:<42} "
        f"run={run_number} "
        f"candidate={candidate_count} "
        f"pred={predicted} "
        f"actual={actual} "
        f"status={status} "
        f"v2={v2_ids}"
    )

    return (
        candidate_count,
        len(v2_ids),
    )


# ============================================================
# MAIN
# ============================================================


def main() -> None:

    total_requests = 0
    successful_requests = 0
    failed_requests = 0

    no_candidate_count = 0
    total_v2_samples = 0

    status_counts = {
        "RECOMMENDED": 0,
        "REVIEW": 0,
        "REJECTED": 0,
        "UNKNOWN": 0,
    }

    families = QUERY_FAMILIES.copy()

    random.shuffle(
        families
    )

    print()
    print(
        "=" * 90
    )

    print(
        "DBOptima - V2 Diverse Training Dataset Generator"
    )

    print(
        "=" * 90
    )

    print(
        f"Families:          {len(families)}"
    )

    print(
        f"Runs per family:   {RUNS_PER_FAMILY}"
    )

    print(
        f"Expected requests: "
        f"{len(families) * RUNS_PER_FAMILY}"
    )

    print(
        "=" * 90
    )

    for family_index, family in enumerate(
        families,
        start=1,
    ):

        print()

        print(
            f"[FAMILY "
            f"{family_index}/"
            f"{len(families)}] "
            f"{family.name}"
        )

        for run_index in range(
            RUNS_PER_FAMILY
        ):

            total_requests += 1

            try:

                query = family.builder(
                    run_index
                )

                response = optimize_query(
                    query=query
                )

                successful_requests += 1

                candidate_count, new_v2 = (
                    print_result(
                        family_name=family.name,
                        run_number=run_index + 1,
                        response=response,
                    )
                )

                total_v2_samples += (
                    new_v2
                )

                if candidate_count == 0:
                    no_candidate_count += 1

                candidates = (
                    response.get(
                        "candidates",
                        [],
                    )
                    or []
                )

                if candidates:

                    status = (
                        candidates[0]
                        .get(
                            "decision",
                            {},
                        )
                        .get(
                            "status",
                            "UNKNOWN",
                        )
                    )

                    if status not in status_counts:
                        status = "UNKNOWN"

                    status_counts[
                        status
                    ] += 1

            except urllib.error.HTTPError as exc:

                failed_requests += 1

                body = exc.read().decode(
                    "utf-8",
                    errors="replace",
                )

                print(
                    f"[HTTP ERROR] "
                    f"{family.name} "
                    f"run={run_index + 1} "
                    f"status={exc.code}"
                )

                print(
                    body
                )

            except urllib.error.URLError as exc:

                failed_requests += 1

                print(
                    f"[CONNECTION ERROR] "
                    f"{family.name} "
                    f"run={run_index + 1}: "
                    f"{exc}"
                )

            except Exception as exc:

                failed_requests += 1

                print(
                    f"[ERROR] "
                    f"{family.name} "
                    f"run={run_index + 1}: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

            time.sleep(
                SLEEP_BETWEEN_REQUESTS
            )

    print()

    print(
        "=" * 90
    )

    print(
        "SUMMARY"
    )

    print(
        "=" * 90
    )

    print(
        f"Families:             "
        f"{len(families)}"
    )

    print(
        f"Total requests:       "
        f"{total_requests}"
    )

    print(
        f"Successful requests:  "
        f"{successful_requests}"
    )

    print(
        f"Failed requests:      "
        f"{failed_requests}"
    )

    print(
        f"No candidate:         "
        f"{no_candidate_count}"
    )

    print(
        f"New V2 samples:       "
        f"{total_v2_samples}"
    )

    print()

    print(
        "STATUS DISTRIBUTION"
    )

    print(
        f"RECOMMENDED:          "
        f"{status_counts['RECOMMENDED']}"
    )

    print(
        f"REVIEW:               "
        f"{status_counts['REVIEW']}"
    )

    print(
        f"REJECTED:             "
        f"{status_counts['REJECTED']}"
    )

    print(
        f"UNKNOWN:              "
        f"{status_counts['UNKNOWN']}"
    )

    print(
        "=" * 90
    )


if __name__ == "__main__":
    main()