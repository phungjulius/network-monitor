#!/usr/bin/env python3
"""
Main entrypoint.
Runs measurements → validates results → prints report → exits with code 1 if any rule fails.
The non-zero exit code is what makes the CI/CD pipeline go red on failures.
"""

import json
import sys
from pathlib import Path
from monitor import run_all_measurements, save_report
from validator import run_validation, summarise

def main():
    # 1. Collect measurements
    report = run_all_measurements()

    # 2. Save raw JSON report
    save_report(report)

    # 3. Run validation framework
    print("\n── Validation results ───────────────────────────────")
    results = run_validation(report)
    for r in results:
        print(f"  {r}")

    # 4. Print summary
    summary = summarise(results)
    print(f"\n── Summary ──────────────────────────────────────────")
    print(f"  Total checks : {summary['total']}")
    print(f"  Passed       : {summary['passed']}")
    print(f"  Failed       : {summary['failed']}")

    if summary["ok"]:
        print("\n  ALL CHECKS PASSED")
        sys.exit(0)
    else:
        print(f"\n  {summary['failed']} CHECK(S) FAILED — see above for details")
        sys.exit(1)   # non-zero exit → CI pipeline marks the run as failed


if __name__ == "__main__":
    main()
