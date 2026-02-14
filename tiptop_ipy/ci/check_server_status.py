#!/usr/bin/env python3
"""Check instrument status against the live TIPTOP server.

Standalone script that tests each instrument template and writes
JSON status files for shields.io badges.

Usage::

    python tiptop_ipy/ci/check_server_status.py --output-dir status
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone


def make_badge(label, status):
    """Return a shields.io endpoint badge dict."""
    if status == "pass":
        return {"schemaVersion": 1, "label": label,
                "message": "passing", "color": "brightgreen"}
    if status == "fail":
        return {"schemaVersion": 1, "label": label,
                "message": "failing", "color": "red"}
    return {"schemaVersion": 1, "label": label,
            "message": "unknown", "color": "lightgrey"}


def check_instruments(output_dir):
    """Run all instrument checks and write results."""
    from tiptop_ipy import TipTop

    os.makedirs(os.path.join(output_dir, "badges"), exist_ok=True)

    # Load previous results for regression detection
    status_path = os.path.join(output_dir, "instrument_status.json")
    previous = {}
    if os.path.exists(status_path):
        with open(status_path) as f:
            prev_data = json.load(f)
        for entry in prev_data.get("instruments", []):
            previous[entry["name"]] = entry["status"]

    # Check server availability
    server_up = TipTop.ping()
    instruments = TipTop.list_instruments()

    results = []
    new_failures = False

    if not server_up:
        print("Server is down, marking all instruments as server_down")
        for name in instruments:
            results.append({
                "name": name,
                "status": "server_down",
                "strehl": None,
                "fwhm": None,
                "elapsed_seconds": 0,
                "error": "Server unreachable",
            })
            badge = make_badge(name, "server_down")
            badge_path = os.path.join(output_dir, "badges", f"{name}.json")
            with open(badge_path, "w") as f:
                json.dump(badge, f, indent=2)
    else:
        for name in instruments:
            print(f"Checking {name}...", end=" ", flush=True)
            t0 = time.time()
            try:
                tt = TipTop(name)
                result = tt.generate_psf(timeout=300)
                elapsed = time.time() - t0
                strehl = result.strehl.tolist()
                fwhm = result.fwhm.tolist()
                status = "pass"
                error = None
                print(f"OK ({elapsed:.1f}s)")
            except Exception as exc:
                elapsed = time.time() - t0
                status = "fail"
                strehl = None
                fwhm = None
                error = str(exc)[:500]
                print(f"FAIL ({elapsed:.1f}s): {error[:80]}")

            results.append({
                "name": name,
                "status": status,
                "strehl": strehl,
                "fwhm": fwhm,
                "elapsed_seconds": round(elapsed, 1),
                "error": error,
            })

            badge = make_badge(name, status)
            badge_path = os.path.join(output_dir, "badges", f"{name}.json")
            with open(badge_path, "w") as f:
                json.dump(badge, f, indent=2)

            # Check for regression
            if status == "fail" and previous.get(name) == "pass":
                new_failures = True

    # Summary
    counts = {"pass": 0, "fail": 0, "server_down": 0}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server_reachable": server_up,
        "summary": counts,
        "instruments": results,
    }

    with open(status_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone: {counts['pass']} pass, {counts['fail']} fail, "
          f"{counts['server_down']} server_down")

    if new_failures:
        print("New failures detected (previously passing instruments now failing)")
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Check TIPTOP instrument status")
    parser.add_argument("--output-dir", default="status",
                        help="Directory for output files (default: status)")
    args = parser.parse_args()
    sys.exit(check_instruments(args.output_dir))


if __name__ == "__main__":
    main()
