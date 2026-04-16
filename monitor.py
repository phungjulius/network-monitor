#!/usr/bin/env python3
"""
Network Performance Monitor
Measures latency (ping) and bandwidth indicators across multiple targets.
Results are validated and saved as structured JSON reports.
"""

import subprocess
import socket
import time
import json
import statistics
import platform
import re
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────

TARGETS = [
    {"name": "Google DNS",      "host": "8.8.8.8"},
    {"name": "Cloudflare DNS",  "host": "1.1.1.1"},
    {"name": "OpenDNS",         "host": "208.67.222.222"},
]

DNS_TARGETS = [
    {"domain": "google.com",   "server": "8.8.8.8"},
    {"domain": "github.com",   "server": "1.1.1.1"},
]

PING_COUNT         = 5       # pings per target
PING_TIMEOUT       = 3       # seconds
TCP_PORT           = 53      # port used for TCP latency probe
TCP_TIMEOUT        = 3       # seconds
REPORT_DIR         = Path("reports")

# ── Ping measurement ─────────────────────────────────────────────────────────

def ping_host(host: str, count: int = PING_COUNT) -> dict:
    """Run system ping and parse RTT values (ms)."""
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", str(count), host]
    else:
        cmd = ["ping", "-c", str(count), "-W", str(PING_TIMEOUT), host]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=PING_TIMEOUT * count + 5,
        )
        output = result.stdout + result.stderr
        rtts = [float(x) for x in re.findall(r"time[=<](\d+\.?\d*)", output)]

        if not rtts:
            return {"success": False, "error": "no RTT values parsed", "raw": output[:300]}

        return {
            "success":     True,
            "rtts_ms":     rtts,
            "min_ms":      round(min(rtts), 2),
            "max_ms":      round(max(rtts), 2),
            "avg_ms":      round(statistics.mean(rtts), 2),
            "jitter_ms":   round(statistics.stdev(rtts), 2) if len(rtts) > 1 else 0.0,
            "packet_loss": round((count - len(rtts)) / count * 100, 1),
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "ping timed out"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# ── TCP latency probe ─────────────────────────────────────────────────────────

def tcp_latency(host: str, port: int = TCP_PORT, samples: int = 3) -> dict:
    """Measure TCP connection establishment time in ms."""
    rtts = []
    for _ in range(samples):
        try:
            start = time.perf_counter()
            with socket.create_connection((host, port), timeout=TCP_TIMEOUT):
                elapsed = (time.perf_counter() - start) * 1000
                rtts.append(round(elapsed, 2))
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    return {
        "success":   True,
        "port":      port,
        "samples":   samples,
        "min_ms":    round(min(rtts), 2),
        "max_ms":    round(max(rtts), 2),
        "avg_ms":    round(statistics.mean(rtts), 2),
        "jitter_ms": round(statistics.stdev(rtts), 2) if len(rtts) > 1 else 0.0,
    }


# ── DNS resolution timing ────────────────────────────────────────────────────

def dns_resolve_time(domain: str) -> dict:
    """Measure how long DNS resolution takes in ms."""
    try:
        start = time.perf_counter()
        ip = socket.gethostbyname(domain)
        elapsed = (time.perf_counter() - start) * 1000
        return {"success": True, "domain": domain, "resolved_ip": ip, "time_ms": round(elapsed, 2)}
    except Exception as exc:
        return {"success": False, "domain": domain, "error": str(exc)}


# ── Report builder ───────────────────────────────────────────────────────────

def run_all_measurements() -> dict:
    """Collect all metrics and return as a structured report dict."""
    print("Starting network performance measurements...")
    timestamp = datetime.now(timezone.utc).isoformat()
    report = {
        "timestamp":   timestamp,
        "ping_results":  [],
        "tcp_results":   [],
        "dns_results":   [],
    }

    for target in TARGETS:
        print(f"  Pinging {target['name']} ({target['host']})...")
        ping = ping_host(target["host"])
        report["ping_results"].append({"target": target["name"], "host": target["host"], **ping})

    for target in TARGETS:
        print(f"  TCP probe → {target['name']}:{TCP_PORT}...")
        tcp = tcp_latency(target["host"])
        report["tcp_results"].append({"target": target["name"], "host": target["host"], **tcp})

    for t in DNS_TARGETS:
        print(f"  DNS resolve → {t['domain']}...")
        dns = dns_resolve_time(t["domain"])
        report["dns_results"].append(dns)

    return report


def save_report(report: dict) -> Path:
    REPORT_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"network_report_{ts}.json"
    path.write_text(json.dumps(report, indent=2))
    print(f"\nReport saved → {path}")
    return path


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    report = run_all_measurements()
    save_report(report)
    print("\nSummary:")
    for r in report["ping_results"]:
        status = "OK" if r.get("success") else "FAIL"
        avg    = r.get("avg_ms", "N/A")
        loss   = r.get("packet_loss", "N/A")
        print(f"  [{status}] {r['target']:20s}  avg={avg} ms  loss={loss}%")
