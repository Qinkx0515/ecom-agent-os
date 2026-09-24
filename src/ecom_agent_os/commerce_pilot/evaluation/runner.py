import argparse
import json
import time

from datetime import datetime
from pathlib import Path

from ecom_agent_os.commerce_pilot.evaluation.comparator import (
    results_equivalent,
)
from ecom_agent_os.commerce_pilot.evaluation.loader import (
    load_jsonl,
)
from ecom_agent_os.commerce_pilot.evaluation.models import (
    AnalyticsEvalCase,
    AnalyticsEvalResult,
    RoutingEvalCase,
    RoutingEvalResult,
)
from ecom_agent_os.commerce_pilot.sql.executor import (
    execute_safe_sql,
)
from ecom_agent_os.commerce_pilot.supervisor.router import (
    route_request,
)
from ecom_agent_os.commerce_pilot.workflow.builder import (
    build_commerce_graph,
)


PROJECT_ROOT = Path(
    __file__
).resolve().parents[4]


DATASET_DIR = (
    PROJECT_ROOT
    / "evals"
    / "datasets"
)


REPORT_DIR = (
    PROJECT_ROOT
    / "evals"
    / "reports"
)


def run_routing_eval():
    cases = load_jsonl(
        DATASET_DIR
        / "routing.jsonl",
        RoutingEvalCase,
    )

    results: list[
        RoutingEvalResult
    ] = []

    for index, case in enumerate(
            cases,
            start=1,
    ):

        print(
            f"[Routing "
            f"{index}/{len(cases)}] "
            f"{case.id}"
        )

        start = (
            time.perf_counter()
        )

        predicted_route = None

        error = None

        try:

            decision = (
                route_request(
                    case.question
                )
            )

            predicted_route = (
                decision.route
            )

        except Exception as exc:

            error = str(
                exc
            )

        latency_ms = (
                (
                        time.perf_counter()
                        - start
                )
                * 1000
        )

        correct = (
                predicted_route
                ==
                case.expected_route
        )

        results.append(
            RoutingEvalResult(
                id=case.id,
                question=case.question,
                expected_route=(
                    case.expected_route
                ),
                predicted_route=(
                    predicted_route
                ),
                correct=correct,
                latency_ms=round(
                    latency_ms,
                    2,
                ),
                error=error,
            )
        )

    return results


def run_analytics_eval():

    cases = load_jsonl(
        DATASET_DIR
        / "analytics.jsonl",
        AnalyticsEvalCase,
    )


    graph = (
        build_commerce_graph()
    )


    results: list[
        AnalyticsEvalResult
    ] = []


    for index, case in enumerate(
        cases,
        start=1,
    ):

        print(
            f"[Analytics "
            f"{index}/{len(cases)}] "
            f"{case.id}"
        )


        start = (
            time.perf_counter()
        )


        generated_sql = None

        execution_success = False

        result_correct = False

        task_success = False

        attempts = 0

        error = None


        try:

            # ===== Gold Result =====

            expected_result = (
                execute_safe_sql(
                    case.expected_sql
                )
            )


            # ===== Agent Result =====

            result = graph.invoke(
                {
                    "question":
                        case.question,

                    "max_attempts":
                        3,

                    "attempts":
                        [],
                }
            )


            generated_sql = (
                result.get(
                    "current_sql"
                )
            )


            attempts = int(
                result.get(
                    "attempt_number",
                    0,
                )
            )


            execution_success = (
                result.get(
                    "status"
                )
                in {
                    "success",
                    "partial_success",
                }
            )


            if execution_success:

                actual_rows = (
                    result.get(
                        "rows",
                        [],
                    )
                )


                result_correct = (
                    results_equivalent(
                        actual_rows,
                        expected_result.rows,
                    )
                )


            task_success = (
                execution_success
                and result_correct
            )


            if not task_success:

                error = (
                    result.get(
                        "last_error"
                    )
                )


        except Exception as exc:

            error = str(
                exc
            )


        latency_ms = (
            (
                time.perf_counter()
                - start
            )
            * 1000
        )


        results.append(
            AnalyticsEvalResult(
                id=case.id,
                question=case.question,
                difficulty=(
                    case.difficulty
                ),
                tags=case.tags,
                generated_sql=(
                    generated_sql
                ),
                execution_success=(
                    execution_success
                ),
                result_correct=(
                    result_correct
                ),
                task_success=(
                    task_success
                ),
                attempts=attempts,
                latency_ms=round(
                    latency_ms,
                    2,
                ),
                error=error,
            )
        )


    return results


def summarize_routing(
    results: list[
        RoutingEvalResult
    ],
):

    total = len(
        results
    )

    correct = sum(
        result.correct
        for result in results
    )


    accuracy = (
        correct / total
        if total
        else 0
    )


    avg_latency = (
        sum(
            result.latency_ms
            for result in results
        )
        / total
        if total
        else 0
    )


    return {
        "total": total,

        "correct": correct,

        "routing_accuracy":
            round(
                accuracy,
                4,
            ),

        "average_latency_ms":
            round(
                avg_latency,
                2,
            ),
    }


def summarize_analytics(
    results: list[
        AnalyticsEvalResult
    ],
):

    total = len(
        results
    )


    execution_successes = sum(
        result.execution_success
        for result in results
    )


    correct_results = sum(
        result.result_correct
        for result in results
    )


    task_successes = sum(
        result.task_success
        for result in results
    )


    retry_cases = sum(
        result.attempts > 1
        for result in results
    )


    avg_attempts = (
        sum(
            result.attempts
            for result in results
        )
        / total
        if total
        else 0
    )


    avg_latency = (
        sum(
            result.latency_ms
            for result in results
        )
        / total
        if total
        else 0
    )

    retried = [
        result
        for result in results
        if result.attempts > 1
    ]


    repaired = [
        result
        for result in retried
        if result.task_success
    ]


    repair_success_rate = (
        len(repaired)
        / len(retried)
        if retried
        else None
    )

    return {
        "total":
            total,

        "execution_success_rate":
            round(
                execution_successes
                / total,
                4,
            )
            if total
            else 0,

        "result_accuracy":
            round(
                correct_results
                / total,
                4,
            )
            if total
            else 0,

        "task_success_rate":
            round(
                task_successes
                / total,
                4,
            )
            if total
            else 0,

        "retry_rate":
            round(
                retry_cases
                / total,
                4,
            )
            if total
            else 0,

        "average_attempts":
            round(
                avg_attempts,
                2,
            ),

        "average_latency_ms":
            round(
                avg_latency,
                2,
            ),

        "repair_success_rate":
        (
            round(
                repair_success_rate,
                4,
            )
            if (
                    repair_success_rate
                    is not None
            )
            else None
        ),
    }

def save_report(
    routing_results,
    analytics_results,
):

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    timestamp = (
        datetime.now()
        .strftime(
            "%Y%m%d_%H%M%S"
        )
    )


    report = {
        "generated_at":
            datetime.now()
            .isoformat(),

        "routing": {
            "summary":
                summarize_routing(
                    routing_results
                ),

            "cases": [
                result.model_dump()
                for result
                in routing_results
            ],
        },

        "analytics": {
            "summary":
                summarize_analytics(
                    analytics_results
                ),

            "cases": [
                result.model_dump()
                for result
                in analytics_results
            ],
        },
    }


    report_path = (
        REPORT_DIR
        / f"eval_{timestamp}.json"
    )


    report_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


    return report_path, report

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--routing-only",
        action="store_true",
    )

    parser.add_argument(
        "--analytics-only",
        action="store_true",
    )

    args = parser.parse_args()


    if args.routing_only:

        routing_results = (
            run_routing_eval()
        )

        analytics_results = []

    elif args.analytics_only:

        routing_results = []

        analytics_results = (
            run_analytics_eval()
        )

    else:

        routing_results = (
            run_routing_eval()
        )

        analytics_results = (
            run_analytics_eval()
        )


    report_path, report = (
        save_report(
            routing_results,
            analytics_results,
        )
    )


    print(
        "\n=========================="
    )

    print(
        "CommercePilot Evaluation"
    )

    print(
        "=========================="
    )


    if routing_results:

        print(
            "\nRouting:"
        )

        print(
            json.dumps(
                report[
                    "routing"
                ][
                    "summary"
                ],
                ensure_ascii=False,
                indent=2,
            )
        )


    if analytics_results:

        print(
            "\nAnalytics:"
        )

        print(
            json.dumps(
                report[
                    "analytics"
                ][
                    "summary"
                ],
                ensure_ascii=False,
                indent=2,
            )
        )


    print(
        "\nReport:"
    )

    print(
        report_path
    )


if __name__ == "__main__":
    main()