#!/usr/bin/env python3
"""Lightweight GitHub Actions run monitor.

Features:
- Fetch latest workflow run for a branch and store its ID locally.
- Optional watch mode to poll until completion.

Usage examples:
  python -m scripts.gha_monitor --store
  python -m scripts.gha_monitor --watch --interval 20
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

STATE_DIR = Path(".gha")
STATE_FILE = STATE_DIR / "latest_run.json"
GITHUB_API = "https://api.github.com"


def require_token() -> str:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN (or GH_TOKEN) is required to monitor GitHub Actions runs.")
    return token


def git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()  # noqa: S603,S607


def default_repo() -> str:
    url = git(["config", "--get", "remote.origin.url"])
    # Handle both SSH and HTTPS remote formats
    if url.startswith("git@"):
        # git@github.com:owner/repo.git
        _, rest = url.split(":", 1)
    else:
        # https://github.com/owner/repo.git
        rest = urllib.parse.urlparse(url).path.lstrip("/")
    return rest.removesuffix(".git")


def default_branch() -> str:
    return git(["rev-parse", "--abbrev-ref", "HEAD"])


def api_get(
    path: str, token: str, params: dict[str, str] | None = None
) -> dict:  # pragma: no cover - network boundary
    qs = f"?{urllib.parse.urlencode(params or {})}" if params else ""
    req = urllib.request.Request(
        f"{GITHUB_API}{path}{qs}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:  # pragma: no cover - network errors
        sys.exit(f"GitHub API error {e.code}: {e.read().decode('utf-8')}")


def latest_run(repo: str, branch: str, token: str) -> dict | None:
    data = api_get(
        f"/repos/{repo}/actions/runs",
        token,
        {"branch": branch, "event": "push", "per_page": "1"},
    )
    runs = data.get("workflow_runs") or []
    return runs[0] if runs else None


def store_run(run: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as fh:
        json.dump(
            {"id": run["id"], "status": run["status"], "conclusion": run.get("conclusion")},
            fh,
            indent=2,
        )
    print(f"Stored run id {run['id']} to {STATE_FILE}")


def watch_run(repo: str, run_id: int, token: str, interval: int) -> None:
    print(f"Watching run {run_id} on {repo} (poll every {interval}s)")
    while True:
        run = api_get(f"/repos/{repo}/actions/runs/{run_id}", token)
        status = run.get("status")
        conclusion = run.get("conclusion")
        print(f"Status: {status}, conclusion: {conclusion}")
        if status in {"completed", "failure", "cancelled"}:
            if conclusion not in {"success"}:
                sys.exit(1)
            return
        time.sleep(interval)


def parse_args() -> argparse.Namespace:  # pragma: no cover - CLI wiring
    p = argparse.ArgumentParser(description="Monitor GitHub Actions runs")
    p.add_argument("--repo", default=None, help="owner/repo (default: from git remote)")
    p.add_argument("--branch", default=None, help="branch to check (default: current)")
    p.add_argument(
        "--store", action="store_true", help="store latest run id to .gha/latest_run.json"
    )
    p.add_argument("--watch", action="store_true", help="watch run until completion")
    p.add_argument("--interval", type=int, default=15, help="poll interval seconds for watch mode")
    p.add_argument(
        "--run-id", type=int, default=None, help="specific run id to watch (default: latest)"
    )
    return p.parse_args()


def main() -> None:  # pragma: no cover
    args = parse_args()
    repo = args.repo or default_repo()
    branch = args.branch or default_branch()
    token = require_token()

    run = latest_run(repo, branch, token)
    if not run:
        sys.exit(f"No workflow runs found for {repo}@{branch}")

    print(
        f"Latest run for {repo}@{branch}: id={run['id']} status={run['status']} conclusion={run.get('conclusion')}"
    )

    if args.store:
        store_run(run)

    if args.watch:
        run_id = args.run_id or run["id"]
        watch_run(repo, run_id, token, args.interval)


if __name__ == "__main__":  # pragma: no cover
    main()
