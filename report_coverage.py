import argparse
import json
import logging

import httpx

logger = logging.getLogger("coverage_reporter")
logging.basicConfig(level=logging.INFO)

COVERAGE_FILE_NAME = "coverage.json"


def report_coverage(coverage_reporter_url: str):
    with open(COVERAGE_FILE_NAME, "r") as file:
        coverage_data = json.load(file)

    covered_lines = coverage_data["totals"]["covered_lines"]
    total_lines = coverage_data["totals"]["num_statements"]

    covered_lines_percentage = (covered_lines / total_lines) * 100
    covered_branches_percentage = coverage_data["totals"]["percent_covered"]
    formatted_line_coverage = f"{covered_lines_percentage:.2f}%"
    formatted_branch_coverage = f"{covered_branches_percentage:.2f}%"

    httpx.post(
        coverage_reporter_url,
        json={
            "appName": "opcua-tools",
            "linePercentage": formatted_line_coverage,
            "branchPercentage": formatted_branch_coverage,
            "methodPercentage": "N/A",
        },
    )

    logger.info(
        f"Coverage report sent to Slack! URL: {coverage_reporter_url};\n"
        f"LINE COVERAGE: {formatted_line_coverage}\n"
        f"BRANCH COVERAGE: {formatted_branch_coverage}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--webhook_url",
        type=str,
        help="The URL of the Slack coverage reporter webhook",
    )
    args = parser.parse_args()
    webhook_url = args.webhook_url
    report_coverage(coverage_reporter_url=webhook_url)
