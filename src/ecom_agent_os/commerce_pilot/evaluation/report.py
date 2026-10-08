import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[4]

REPORT_DIR = PROJECT_ROOT / "evals" / "reports"


def percent(
    value: float | None,
) -> str:

    if value is None:
        return "N/A"

    return f"{value * 100:.2f}%"


def percentile(
    values: list[float],
    q: float,
) -> float | None:

    if not values:
        return None

    values = sorted(values)

    index = (len(values) - 1) * q

    lower = int(index)

    upper = min(
        lower + 1,
        len(values) - 1,
    )

    fraction = index - lower

    return values[lower] * (1 - fraction) + values[upper] * fraction


def analytics_by_difficulty(
    cases: list[dict[str, Any]],
) -> dict:

    groups = defaultdict(list)

    for case in cases:
        groups[case["difficulty"]].append(case)

    result = {}

    for (
        difficulty,
        items,
    ) in groups.items():
        total = len(items)

        success = sum(bool(item["task_success"]) for item in items)

        result[difficulty] = {
            "total": total,
            "success": success,
            "task_success_rate": (success / total if total else 0),
        }

    return result


def analytics_by_tag(
    cases: list[dict[str, Any]],
) -> dict:

    tag_stats = defaultdict(
        lambda: {
            "total": 0,
            "success": 0,
        }
    )

    for case in cases:
        for tag in case.get(
            "tags",
            [],
        ):
            tag_stats[tag]["total"] += 1

            if case.get("task_success"):
                tag_stats[tag]["success"] += 1

    result = {}

    for (
        tag,
        stats,
    ) in tag_stats.items():
        total = stats["total"]

        success = stats["success"]

        result[tag] = {
            "total": total,
            "success": success,
            "success_rate": (success / total if total else 0),
        }

    return result


def collect_failures(
    cases: list[dict[str, Any]],
) -> list[dict]:

    return [
        case
        for case in cases
        if not case.get(
            "task_success",
            False,
        )
    ]


def build_markdown_report(
    report: dict,
) -> str:

    routing = report["routing"]

    analytics = report["analytics"]

    routing_summary = routing["summary"]

    analytics_summary = analytics["summary"]

    analytics_cases = analytics["cases"]

    latencies = [
        float(case["latency_ms"])
        for case in analytics_cases
        if case.get("latency_ms") is not None
    ]

    difficulty = analytics_by_difficulty(analytics_cases)

    tag_stats = analytics_by_tag(analytics_cases)

    failures = collect_failures(analytics_cases)

    lines = [
        "# CommercePilot Evaluation Report",
        "",
        f"Generated at: `{report.get('generated_at')}`",
        "",
        "## Overall Metrics",
        "",
        "| Metric | Result |",
        "| --- | ---: |",
        (f"| Routing Accuracy | {percent(routing_summary.get('routing_accuracy'))} |"),
        (
            "| SQL Execution Success | "
            f"{percent(analytics_summary.get('execution_success_rate'))} |"
        ),
        (f"| Result Accuracy | {percent(analytics_summary.get('result_accuracy'))} |"),
        (
            "| Task Success Rate | "
            f"{percent(analytics_summary.get('task_success_rate'))} |"
        ),
        (f"| Retry Rate | {percent(analytics_summary.get('retry_rate'))} |"),
        (
            "| Repair Success Rate | "
            f"{percent(analytics_summary.get('repair_success_rate'))} |"
        ),
        "",
        "## Latency",
        "",
        "| Metric | ms |",
        "| --- | ---: |",
        (
            f"| Mean | {statistics.mean(latencies):.2f} |"
            if latencies
            else "| Mean | N/A |"
        ),
        (
            f"| P50 | {percentile(latencies, 0.50):.2f} |"
            if latencies
            else "| P50 | N/A |"
        ),
        (
            f"| P95 | {percentile(latencies, 0.95):.2f} |"
            if latencies
            else "| P95 | N/A |"
        ),
        "",
        "## Performance by Difficulty",
        "",
        "| Difficulty | Success | Total | Rate |",
        "| --- | ---: | ---: | ---: |",
    ]

    for name in [
        "easy",
        "medium",
        "hard",
    ]:
        if name not in difficulty:
            continue

        item = difficulty[name]

        lines.append(
            "| "
            f"{name.capitalize()} | "
            f"{item['success']} | "
            f"{item['total']} | "
            f"{percent(item['task_success_rate'])} |"
        )

    lines.extend(
        [
            "",
            "## Performance by Tag",
            "",
            "| Tag | Success | Total | Rate |",
            "| --- | ---: | ---: | ---: |",
        ]
    )

    for (
        tag,
        item,
    ) in sorted(tag_stats.items()):
        lines.append(
            "| "
            f"{tag} | "
            f"{item['success']} | "
            f"{item['total']} | "
            f"{percent(item['success_rate'])} |"
        )

    lines.extend(
        [
            "",
            "## Failure Cases",
            "",
        ]
    )

    if not failures:
        lines.append("No failed analytics cases.")

    else:
        for case in failures:
            lines.extend(
                [
                    (f"### {case['id']}"),
                    "",
                    (f"**Question:** {case['question']}"),
                    "",
                    (f"**Difficulty:** {case['difficulty']}"),
                    "",
                    ("**Generated SQL:**"),
                    "",
                    "```sql",
                    (case.get("generated_sql") or "<none>"),
                    "```",
                    "",
                    (f"**Error:** {case.get('error')}"),
                    "",
                ]
            )

    return "\n".join(lines)


def find_latest_report() -> Path:

    files = sorted(REPORT_DIR.glob("eval_*.json"))

    if not files:
        raise RuntimeError("No evaluation report found.")

    return files[-1]


def main():

    source = find_latest_report()

    report = json.loads(source.read_text(encoding="utf-8"))

    markdown = build_markdown_report(report)

    output = REPORT_DIR / "latest.md"

    output.write_text(
        markdown,
        encoding="utf-8",
    )

    print(f"Evaluation report written to: {output}")


if __name__ == "__main__":
    main()
