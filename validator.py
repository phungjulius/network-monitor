"""
Validation Framework
Defines rules that check whether network measurements are within
acceptable thresholds. Each rule is an independent, named validator.
This is what turns raw measurements into pass/fail quality gates.
"""

from dataclasses import dataclass
from typing import Any

# ── Thresholds (edit these to tighten or relax rules) ────────────────────────

THRESHOLDS = {
    "max_avg_latency_ms":    150,   # avg ping RTT must be below this
    "max_jitter_ms":          30,   # jitter (stdev of RTTs) must be below this
    "max_packet_loss_pct":     5,   # packet loss % must be below this
    "max_tcp_avg_ms":        200,   # TCP connection time must be below this
    "max_dns_time_ms":       300,   # DNS resolution must be below this
    "min_successful_targets":  2,   # at least N targets must succeed
}


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    rule:    str
    passed:  bool
    detail:  str
    value:   Any = None
    limit:   Any = None

    def __str__(self):
        icon = "PASS" if self.passed else "FAIL"
        return f"[{icon}] {self.rule}: {self.detail}"


# ── Individual validation rules ───────────────────────────────────────────────

def validate_ping_latency(ping_results: list) -> list[ValidationResult]:
    """Each successful ping target must have avg RTT below the threshold."""
    results = []
    for r in ping_results:
        if not r.get("success"):
            results.append(ValidationResult(
                rule   = f"ping_latency:{r['target']}",
                passed = False,
                detail = f"ping failed — {r.get('error', 'unknown error')}",
            ))
            continue
        avg   = r["avg_ms"]
        limit = THRESHOLDS["max_avg_latency_ms"]
        results.append(ValidationResult(
            rule   = f"ping_latency:{r['target']}",
            passed = avg <= limit,
            detail = f"avg={avg} ms (limit {limit} ms)",
            value  = avg,
            limit  = limit,
        ))
    return results


def validate_jitter(ping_results: list) -> list[ValidationResult]:
    """Jitter (RTT stdev) per target must be below threshold."""
    results = []
    for r in ping_results:
        if not r.get("success"):
            continue
        jitter = r.get("jitter_ms", 0)
        limit  = THRESHOLDS["max_jitter_ms"]
        results.append(ValidationResult(
            rule   = f"jitter:{r['target']}",
            passed = jitter <= limit,
            detail = f"jitter={jitter} ms (limit {limit} ms)",
            value  = jitter,
            limit  = limit,
        ))
    return results


def validate_packet_loss(ping_results: list) -> list[ValidationResult]:
    """Packet loss per target must be below threshold."""
    results = []
    for r in ping_results:
        if not r.get("success"):
            continue
        loss  = r.get("packet_loss", 100)
        limit = THRESHOLDS["max_packet_loss_pct"]
        results.append(ValidationResult(
            rule   = f"packet_loss:{r['target']}",
            passed = loss <= limit,
            detail = f"loss={loss}% (limit {limit}%)",
            value  = loss,
            limit  = limit,
        ))
    return results


def validate_tcp_latency(tcp_results: list) -> list[ValidationResult]:
    """TCP connection time per target must be below threshold."""
    results = []
    for r in tcp_results:
        if not r.get("success"):
            results.append(ValidationResult(
                rule   = f"tcp_latency:{r['target']}",
                passed = False,
                detail = f"TCP probe failed — {r.get('error', 'unknown')}",
            ))
            continue
        avg   = r["avg_ms"]
        limit = THRESHOLDS["max_tcp_avg_ms"]
        results.append(ValidationResult(
            rule   = f"tcp_latency:{r['target']}",
            passed = avg <= limit,
            detail = f"avg={avg} ms (limit {limit} ms)",
            value  = avg,
            limit  = limit,
        ))
    return results


def validate_dns(dns_results: list) -> list[ValidationResult]:
    """DNS resolution time must be below threshold and must succeed."""
    results = []
    for r in dns_results:
        if not r.get("success"):
            results.append(ValidationResult(
                rule   = f"dns:{r['domain']}",
                passed = False,
                detail = f"DNS failed — {r.get('error', 'unknown')}",
            ))
            continue
        t     = r["time_ms"]
        limit = THRESHOLDS["max_dns_time_ms"]
        results.append(ValidationResult(
            rule   = f"dns:{r['domain']}",
            passed = t <= limit,
            detail = f"resolved in {t} ms (limit {limit} ms)",
            value  = t,
            limit  = limit,
        ))
    return results


def validate_minimum_successful_targets(ping_results: list) -> list[ValidationResult]:
    """At least N targets must respond successfully."""
    successes = sum(1 for r in ping_results if r.get("success"))
    limit     = THRESHOLDS["min_successful_targets"]
    return [ValidationResult(
        rule   = "min_successful_targets",
        passed = successes >= limit,
        detail = f"{successes}/{len(ping_results)} targets succeeded (need {limit})",
        value  = successes,
        limit  = limit,
    )]


# ── Framework entry point ─────────────────────────────────────────────────────

def run_validation(report: dict) -> list[ValidationResult]:
    """
    Run all validation rules against a measurement report.
    Returns a flat list of ValidationResult objects.
    """
    all_results: list[ValidationResult] = []
    all_results += validate_ping_latency(report.get("ping_results", []))
    all_results += validate_jitter(report.get("ping_results", []))
    all_results += validate_packet_loss(report.get("ping_results", []))
    all_results += validate_tcp_latency(report.get("tcp_results", []))
    all_results += validate_dns(report.get("dns_results", []))
    all_results += validate_minimum_successful_targets(report.get("ping_results", []))
    return all_results


def summarise(results: list[ValidationResult]) -> dict:
    """Return a pass/fail summary dict."""
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    return {
        "total":  len(results),
        "passed": passed,
        "failed": failed,
        "ok":     failed == 0,
    }
