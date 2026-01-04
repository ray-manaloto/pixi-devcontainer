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
import logging
import os
import ssl
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
logger = logging.getLogger(__name__)
HTTP_ERROR_THRESHOLD = 400


def require_token() -> str:
    """Return a GitHub token or exit with a helpful error."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token is None:
        message = "GITHUB_TOKEN (or GH_TOKEN) is required to monitor GitHub Actions runs."
        raise SystemExit(message)
    return token


def git(args: list[str]) -> str:
    """Run a git command and return stripped stdout."""
    return subprocess.check_output(["git", *args], text=True).strip()  # noqa: S603,S607


def default_repo() -> str:
    """Infer owner/repo from the origin remote."""
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
    """Return the current branch name."""
    return git(["rev-parse", "--abbrev-ref", "HEAD"])


def api_get(
    path: str,
    token: str,
    params: dict[str, str] | None = None,
) -> dict:  # pragma: no cover - network boundary
    """Perform a GitHub API GET with minimal headers."""
    query = urllib.parse.urlencode(params or {})
    query = urllib.parse.urlencode(params or {})
    url = f"{GITHUB_API}{path}"
    if query:
        url = f"{url}?{query}"

    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        message = "Refusing non-https GitHub API URL"
        raise ValueError(message)
    if parsed.netloc != "api.github.com":
        message = f"Unexpected GitHub API host: {parsed.netloc}"
        raise ValueError(message)

    context = ssl.create_default_context()
    try:
        request = urllib.request.Request(  # noqa: S310
            url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        )
        with urllib.request.urlopen(  # nosemgrep  # noqa: S310
            request,
            context=context,
            timeout=10,
        ) as response:
            body = response.read().decode("utf-8")
            if response.status >= HTTP_ERROR_THRESHOLD:
                sys.exit(f"GitHub API error {response.status}: {body}")
            return json.loads(body)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="ignore")
        sys.exit(f"GitHub API error {error.code}: {body}")


def latest_run(repo: str, branch: str, token: str) -> dict | None:
    """Return the latest push workflow run for a branch."""
    data = api_get(
        f"/repos/{repo}/actions/runs",
        token,
        {"branch": branch, "event": "push", "per_page": "1"},
    )
    runs = data.get("workflow_runs") or []
    return runs[0] if runs else None


def store_run(run: dict) -> None:
    """Persist the latest run metadata for follow-up watch commands."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as fh:
        json.dump(
            {"id": run["id"], "status": run["status"], "conclusion": run.get("conclusion")},
            fh,
            indent=2,
        )
    logger.info("Stored run id %s to %s", run["id"], STATE_FILE)


def watch_run(repo: str, run_id: int, token: str, interval: int) -> None:
    """Poll a workflow run until completion; exit non-zero on failure."""
    logger.info("Watching run %s on %s (poll every %ss)", run_id, repo, interval)
    while True:
        run = api_get(f"/repos/{repo}/actions/runs/{run_id}", token)
        status = run.get("status")
        conclusion = run.get("conclusion")
        logger.info("Status: %s, conclusion: %s", status, conclusion)
        if status in {"completed", "failure", "cancelled"}:
            if conclusion not in {"success"}:
                sys.exit(1)
            return
        time.sleep(interval)


def parse_args() -> argparse.Namespace:  # pragma: no cover - CLI wiring
    """Parse CLI arguments."""
    p = argparse.ArgumentParser(description="Monitor GitHub Actions runs")
    p.add_argument("--repo", default=None, help="owner/repo (default: from git remote)")
    p.add_argument("--branch", default=None, help="branch to check (default: current)")
    p.add_argument(
        "--store",
        action="store_true",
        help="store latest run id to .gha/latest_run.json",
    )
    p.add_argument("--watch", action="store_true", help="watch run until completion")
    p.add_argument("--interval", type=int, default=15, help="poll interval seconds for watch mode")
    p.add_argument(
        "--run-id",
        type=int,
        default=None,
        help="specific run id to watch (default: latest)",
    )
    return p.parse_args()


def main() -> None:  # pragma: no cover
    """Entry point for GitHub Actions monitor CLI."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    repo = args.repo or default_repo()
    branch = args.branch or default_branch()
    token = require_token()

    run = latest_run(repo, branch, token)
    if not run:
        message = f"No workflow runs found for {repo}@{branch}"
        raise SystemExit(message)

    logger.info(
        "Latest run for %s@%s: id=%s status=%s conclusion=%s",
        repo,
        branch,
        run["id"],
        run["status"],
        run.get("conclusion"),
    )

    if args.store:
        store_run(run)

    if args.watch:
        run_id = args.run_id or run["id"]
        if run_id is None:
            message = "Run id missing; cannot watch workflow."
            raise SystemExit(message)
        watch_run(repo, run_id, token, args.interval)


if __name__ == "__main__":  # pragma: no cover
    main()
