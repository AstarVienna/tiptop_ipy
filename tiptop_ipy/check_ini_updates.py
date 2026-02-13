"""
Fetch the latest AO instrument .ini files from the TIPTOP GitHub repo
and compare them against the local copies in instrument_templates/.

Source: https://github.com/astro-tiptop/TIPTOP/tree/main/tiptop/perfTest

Usage:
    python -m tiptop_ipy.check_ini_updates          # check for differences
    python -m tiptop_ipy.check_ini_updates --update  # overwrite local files with remote
"""

import argparse
import os
import os.path as p
import re
import sys

import requests

GITHUB_API_URL = (
    "https://api.github.com/repos/astro-tiptop/TIPTOP"
    "/contents/tiptop/perfTest"
)
GITHUB_RAW_BASE = (
    "https://raw.githubusercontent.com/astro-tiptop/TIPTOP"
    "/refs/heads/main/tiptop/perfTest"
)
TEMPLATES_DIR = p.join(p.dirname(__file__), "instrument_templates")

# Files in the remote perfTest/ directory that we skip
SKIP_FILES = {"dummy.ini", "MAVIStest.ini"}


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def list_remote_ini_files(api_url: str = GITHUB_API_URL) -> list[str]:
    """Use the GitHub API to list .ini filenames in the perfTest directory."""
    resp = requests.get(api_url, timeout=15)
    resp.raise_for_status()
    return [
        item["name"]
        for item in resp.json()
        if item["name"].endswith(".ini") and item["name"] not in SKIP_FILES
    ]


def fetch_ini_file(filename: str, raw_base: str = GITHUB_RAW_BASE) -> str:
    """Fetch a single .ini file from GitHub raw content."""
    url = f"{raw_base}/{filename}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.text


def fetch_all_ini_files(
    api_url: str = GITHUB_API_URL,
    raw_base: str = GITHUB_RAW_BASE,
) -> dict[str, str]:
    """
    Fetch all .ini files from the TIPTOP perfTest directory.

    Returns a dict of {filename: ini_contents}.
    """
    filenames = list_remote_ini_files(api_url)
    remote = {}
    for fname in filenames:
        remote[fname] = fetch_ini_file(fname, raw_base)
    return remote


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    """Normalise ini content for comparison: strip comment-only lines,
    trailing whitespace, and collapse blank lines."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(";") or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def compare_ini_files(
    remote: dict[str, str],
    templates_dir: str = TEMPLATES_DIR,
) -> dict[str, str]:
    """
    Compare remote ini files against local ones.

    Returns a dict of {filename: status} where status is one of:
        'up-to-date'   - local matches remote
        'changed'      - local exists but differs
        'new'          - remote file not found locally
        'local-only'   - local file has no remote equivalent
    """
    results = {}

    for fname, remote_content in sorted(remote.items()):
        local_path = p.join(templates_dir, fname)
        if not p.isfile(local_path):
            results[fname] = "new"
        else:
            with open(local_path, "r", encoding="utf-8") as f:
                local_content = f.read()
            if _normalise(local_content) == _normalise(remote_content):
                results[fname] = "up-to-date"
            else:
                results[fname] = "changed"

    for fname in sorted(os.listdir(templates_dir)):
        if not fname.endswith(".ini"):
            continue
        if fname not in remote:
            results[fname] = "local-only"

    return results


def update_local_files(
    remote: dict[str, str],
    templates_dir: str = TEMPLATES_DIR,
) -> list[str]:
    """Write remote ini files to the local templates directory.
    Returns list of filenames that were written."""
    written = []
    for fname, content in sorted(remote.items()):
        fpath = p.join(templates_dir, fname)
        with open(fpath, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        written.append(fname)
    return written


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Check for updates to TIPTOP instrument .ini files"
    )
    ap.add_argument(
        "--update",
        action="store_true",
        help="Overwrite local ini files with the latest from GitHub",
    )
    args = ap.parse_args()

    print(f"Fetching ini file list from GitHub...\n")
    try:
        remote = fetch_all_ini_files()
    except requests.RequestException as e:
        print(f"ERROR: Could not reach GitHub: {e}")
        sys.exit(1)

    if not remote:
        print("ERROR: No ini files found in the remote repo.")
        sys.exit(1)

    print(f"Found {len(remote)} instrument configs on GitHub:")
    for fname in sorted(remote):
        print(f"  {fname}")
    print()

    results = compare_ini_files(remote)

    any_differences = False
    for fname, status in sorted(results.items()):
        icon = {
            "up-to-date": "  OK",
            "changed":    "DIFF",
            "new":        " NEW",
            "local-only": " LOC",
        }.get(status, "  ??")
        print(f"  [{icon}] {fname}")
        if status in ("changed", "new"):
            any_differences = True

    print()
    if not any_differences:
        print("All local ini files are up to date.")
    elif args.update:
        written = update_local_files(remote)
        print(f"Updated {len(written)} files:")
        for fname in written:
            print(f"  {fname}")
    else:
        print("Run with --update to overwrite local files with remote versions.")


if __name__ == "__main__":
    main()
