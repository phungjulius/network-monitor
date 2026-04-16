"""
Test suite for the validation framework.
Uses pytest to verify that each rule correctly catches bad data
and correctly passes good data.
Run with: pytest tests/ -v
"""

import pytest
from validator import (
    validate_ping_latency,
    validate_jitter,
    validate_packet_loss,
    validate_tcp_latency,
    validate_dns,
    validate_minimum_successful_targets,
    run_validation,
    summarise,
    THRESHOLDS,
)

# ── Fixtures: sample data ─────────────────────────────────────────────────────

GOOD_PING = [
    {
        "target": "Google DNS", "host": "8.8.8.8",
        "success": True, "avg_ms": 10.0, "jitter_ms": 2.0,
        "packet_loss": 0.0, "rtts_ms": [9.5, 10.2, 10.3],
    },
    {
        "target": "Cloudflare DNS", "host": "1.1.1.1",
        "success": True, "avg_ms": 12.0, "jitter_ms": 1.5,
        "packet_loss": 0.0, "rtts_ms": [11.8, 12.1, 12.1],
    },
]

BAD_PING_HIGH_LATENCY = [
    {
        "target": "Slow Host", "host": "192.0.2.1",
        "success": True, "avg_ms": 999.0, "jitter_ms": 50.0,
        "packet_loss": 40.0, "rtts_ms": [950.0, 1000.0, 1047.0],
    },
]

FAILED_PING = [
    {"target": "Dead Host", "host": "192.0.2.99", "success": False, "error": "request timeout"},
]

GOOD_TCP = [
    {"target": "Google DNS", "host": "8.8.8.8", "success": True, "avg_ms": 15.0, "jitter_ms": 1.0, "port": 53},
]

BAD_TCP = [
    {"target": "Google DNS", "host": "8.8.8.8", "success": True, "avg_ms": 999.0, "jitter_ms": 1.0, "port": 53},
]

FAILED_TCP = [
    {"target": "Dead", "host": "192.0.2.99", "success": False, "error": "connection refused"},
]

GOOD_DNS = [
    {"success": True, "domain": "google.com", "resolved_ip": "142.250.74.46", "time_ms": 20.0},
]

BAD_DNS = [
    {"success": True, "domain": "google.com", "resolved_ip": "142.250.74.46", "time_ms": 999.0},
]

FAILED_DNS = [
    {"success": False, "domain": "nonexistent.invalid", "error": "Name or service not known"},
]


# ── Ping latency tests ────────────────────────────────────────────────────────

class TestPingLatency:
    def test_passes_with_low_latency(self):
        results = validate_ping_latency(GOOD_PING)
        assert all(r.passed for r in results)

    def test_fails_with_high_latency(self):
        results = validate_ping_latency(BAD_PING_HIGH_LATENCY)
        assert any(not r.passed for r in results)

    def test_fails_when_ping_unreachable(self):
        results = validate_ping_latency(FAILED_PING)
        assert all(not r.passed for r in results)

    def test_result_rule_name_includes_target(self):
        results = validate_ping_latency(GOOD_PING)
        assert "Google DNS" in results[0].rule

    def test_value_stored_correctly(self):
        results = validate_ping_latency(GOOD_PING)
        assert results[0].value == GOOD_PING[0]["avg_ms"]


# ── Jitter tests ──────────────────────────────────────────────────────────────

class TestJitter:
    def test_passes_with_low_jitter(self):
        results = validate_jitter(GOOD_PING)
        assert all(r.passed for r in results)

    def test_fails_with_high_jitter(self):
        results = validate_jitter(BAD_PING_HIGH_LATENCY)
        assert any(not r.passed for r in results)

    def test_skips_failed_pings(self):
        results = validate_jitter(FAILED_PING)
        assert len(results) == 0


# ── Packet loss tests ─────────────────────────────────────────────────────────

class TestPacketLoss:
    def test_passes_with_zero_loss(self):
        results = validate_packet_loss(GOOD_PING)
        assert all(r.passed for r in results)

    def test_fails_with_high_loss(self):
        results = validate_packet_loss(BAD_PING_HIGH_LATENCY)
        assert any(not r.passed for r in results)

    def test_limit_matches_threshold(self):
        results = validate_packet_loss(GOOD_PING)
        assert results[0].limit == THRESHOLDS["max_packet_loss_pct"]


# ── TCP latency tests ─────────────────────────────────────────────────────────

class TestTCPLatency:
    def test_passes_with_good_tcp(self):
        results = validate_tcp_latency(GOOD_TCP)
        assert all(r.passed for r in results)

    def test_fails_with_slow_tcp(self):
        results = validate_tcp_latency(BAD_TCP)
        assert any(not r.passed for r in results)

    def test_fails_when_connection_refused(self):
        results = validate_tcp_latency(FAILED_TCP)
        assert all(not r.passed for r in results)


# ── DNS tests ─────────────────────────────────────────────────────────────────

class TestDNS:
    def test_passes_with_fast_dns(self):
        results = validate_dns(GOOD_DNS)
        assert all(r.passed for r in results)

    def test_fails_with_slow_dns(self):
        results = validate_dns(BAD_DNS)
        assert any(not r.passed for r in results)

    def test_fails_when_dns_resolution_fails(self):
        results = validate_dns(FAILED_DNS)
        assert all(not r.passed for r in results)


# ── Minimum targets test ──────────────────────────────────────────────────────

class TestMinimumSuccessfulTargets:
    def test_passes_when_enough_targets_succeed(self):
        results = validate_minimum_successful_targets(GOOD_PING)
        assert results[0].passed

    def test_fails_when_too_few_targets_succeed(self):
        results = validate_minimum_successful_targets(FAILED_PING)
        assert not results[0].passed


# ── Full framework integration test ───────────────────────────────────────────

class TestFullFramework:
    def test_all_pass_with_good_report(self):
        report = {
            "ping_results": GOOD_PING,
            "tcp_results":  GOOD_TCP,
            "dns_results":  GOOD_DNS,
        }
        results = run_validation(report)
        summary = summarise(results)
        assert summary["failed"] == 0
        assert summary["ok"] is True

    def test_failures_detected_with_bad_report(self):
        report = {
            "ping_results": BAD_PING_HIGH_LATENCY,
            "tcp_results":  BAD_TCP,
            "dns_results":  BAD_DNS,
        }
        results = run_validation(report)
        summary = summarise(results)
        assert summary["failed"] > 0
        assert summary["ok"] is False

    def test_summarise_counts_correctly(self):
        report = {
            "ping_results": GOOD_PING + FAILED_PING,
            "tcp_results":  GOOD_TCP,
            "dns_results":  GOOD_DNS,
        }
        results  = run_validation(report)
        summary  = summarise(results)
        assert summary["total"] == summary["passed"] + summary["failed"]
