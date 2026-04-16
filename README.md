# Network Performance Monitor

A Python-based automated tool that measures **latency**, **jitter**, **packet loss**, and **DNS resolution time** across multiple network targets, validates results against configurable thresholds, and reports pass/fail status — all running inside a **CI/CD pipeline on Linux**.

Built as a personal learning project to practice:
- Automated testing and validation frameworks (pytest)
- CI/CD pipeline design (GitHub Actions on Ubuntu)
- Python scripting and Bash automation
- Systematic measurement, documentation, and reporting

---

## What it does

1. **Measures** — pings multiple DNS servers, probes TCP connection time, and times DNS resolution
2. **Validates** — runs each metric through a rule-based validation framework with configurable thresholds
3. **Reports** — saves structured JSON reports and prints a pass/fail summary
4. **Automates** — GitHub Actions runs the full pipeline on every push and on a schedule (every 6 hours)

---

## Project structure

```
network-monitor/
├── monitor.py              # Measurement engine (ping, TCP, DNS)
├── validator.py            # Validation framework (rules + thresholds)
├── main.py                 # Entrypoint: runs measurements → validates → exits
├── setup_and_run.sh        # Bash script: installs deps, runs tests, runs monitor
├── requirements.txt        # Python dependencies
├── pytest.ini              # pytest configuration
├── tests/
│   └── test_validator.py   # Unit tests for all validation rules
├── reports/                # Auto-generated JSON reports (git-ignored)
└── .github/
    └── workflows/
        └── ci.yml          # GitHub Actions CI/CD pipeline
```

---

## How to run locally

**Requirements:** Python 3.10+, Linux or macOS (Windows: WSL recommended)

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/network-monitor.git
cd network-monitor

# Install dependencies
pip install -r requirements.txt

# Run unit tests only
pytest tests/ -v

# Run the full monitor (measurements + validation)
python main.py

# Or use the Bash script (installs deps + runs tests + runs monitor)
bash setup_and_run.sh
```

---

## CI/CD pipeline

Every `git push` to `main` triggers GitHub Actions to:

1. Spin up a clean **Ubuntu Linux** environment
2. Install Python 3.11 and dependencies
3. Run all **unit tests** (pytest)
4. Run live **network measurements** and validation
5. Upload test results and JSON reports as artifacts
6. Mark the run **green** (all pass) or **red** (any failure)

The pipeline also runs automatically **every 6 hours** via a scheduled cron trigger.

See `.github/workflows/ci.yml` for the full pipeline definition.

---

## Validation framework

`validator.py` defines independent, named rules. Each rule takes measurement data and returns a `ValidationResult` with:
- `rule` — the name of the check
- `passed` — True/False
- `detail` — human-readable explanation
- `value` / `limit` — actual vs. threshold

### Default thresholds

| Metric | Threshold |
|---|---|
| Average ping latency | ≤ 150 ms |
| Jitter (RTT stdev) | ≤ 30 ms |
| Packet loss | ≤ 5 % |
| TCP connection time | ≤ 200 ms |
| DNS resolution time | ≤ 300 ms |
| Minimum reachable targets | ≥ 2 |

Edit the `THRESHOLDS` dict in `validator.py` to adjust any limit.

---

## Example output

```
Starting network performance measurements...
  Pinging Google DNS (8.8.8.8)...
  Pinging Cloudflare DNS (1.1.1.1)...
  TCP probe → Google DNS:53...
  DNS resolve → google.com...

Report saved → reports/network_report_20260410_143022.json

── Validation results ───────────────────────────────
  [PASS] ping_latency:Google DNS: avg=11.2 ms (limit 150 ms)
  [PASS] ping_latency:Cloudflare DNS: avg=9.8 ms (limit 150 ms)
  [PASS] jitter:Google DNS: jitter=1.4 ms (limit 30 ms)
  [PASS] packet_loss:Google DNS: loss=0.0% (limit 5%)
  [PASS] tcp_latency:Google DNS: avg=14.3 ms (limit 200 ms)
  [PASS] dns:google.com: resolved in 22.1 ms (limit 300 ms)
  [PASS] min_successful_targets: 2/2 targets succeeded (need 2)

── Summary ──────────────────────────────────────────
  Total checks : 13
  Passed       : 13
  Failed       : 0

  ALL CHECKS PASSED
```

---

## Author

Julius Phung — MSc Communications Engineering student, Aalto University
