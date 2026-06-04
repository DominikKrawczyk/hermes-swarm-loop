"""
git_push.py — GitHub Push Pipeline for Hermes Swarm Loop
========================================================
Pushes the framework or project repo via gh API (blob→tree→commit→ref).
Auto-commits use the agents' own commits if present; otherwise creates
a phase-level commit.

Usage:
  from engine.git_push import git_push_repo

  git_push_repo("/root/code/hermes-swarm-loop", "Auto-update: Phase development setup complete")
"""

import json
import os
import shutil
import subprocess
import time
from pathlib import Path


def run(cmd, timeout=30, cwd=None):
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=cwd
        )
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]", -1
    except Exception as e:
        return f"[ERROR {e}]", -1


def git_push_repo(repo_path: str, message: str = "", remote: str = "origin", branch: str = "main") -> bool:
    """
    Push the repo at repo_path to GitHub.
    Returns True on success.
    """
    repo = Path(repo_path)
    if not (repo / ".git").exists():
        print(f"  No .git at {repo_path}")
        return False

    # 1. Stage all changes
    out, code = run("git add -A", timeout=30, cwd=str(repo))
    if code != 0:
        print(f"  git add failed: {out[:200]}")
        return False

    # 2. Check if anything changed
    out, code = run("git diff --cached --stat", timeout=10, cwd=str(repo))
    if not out.strip():
        out, code = run("git status --porcelain", timeout=10, cwd=str(repo))
        if not out.strip():
            print(f"  Nothing to commit at {repo_path}")
            # Still try to push in case local is ahead
            out, code = run(f"git push {remote} {branch} 2>&1", timeout=60, cwd=str(repo))
            if "Everything up-to-date" in out or code == 0:
                return True
            return False

    # 3. Check if agents already committed
    out, code = run("git log --oneline -1", timeout=10, cwd=str(repo))
    if code == 0 and out.strip():
        # Agents auto-commit — check if there are uncommitted changes
        out, code = run("git status --porcelain", timeout=10, cwd=str(repo))
        if not out.strip() and message:
            # No uncommitted changes but we have a message — push what's there
            out, code = run(f"git push {remote} {branch} 2>&1", timeout=60, cwd=str(repo))
            if "Everything up-to-date" in out or code == 0:
                print(f"  ✅ Pushed (up-to-date or OK): {out[:100]}")
                return True

    # 4. Commit (if there are staged changes)
    out, code = run("git diff --cached --stat", timeout=10, cwd=str(repo))
    if out.strip():
        msg = message or f"🔥 Hermes Swarm Loop — auto-update"
        # Escape quotes for shell
        msg_escaped = msg.replace('"', '\\"')
        out, code = run(f'git commit -m "{msg_escaped}" 2>&1', timeout=30, cwd=str(repo))
        if code != 0 and "nothing to commit" not in out:
            print(f"  git commit: {out[:200]}")
            # Try with explicit author
            out, code = run(
                f'git -c user.name="Hermes Swarm" -c user.email="hermes@swarm.loop" commit -m "{msg_escaped}" 2>&1',
                timeout=30, cwd=str(repo)
            )

    # 5. Push
    out, code = run(f"git push {remote} {branch} 2>&1", timeout=120, cwd=str(repo))
    if code == 0 or "Everything up-to-date" in out:
        print(f"  ✅ Pushed to {remote}/{branch}")
        return True
    else:
        print(f"  ❌ Push failed: {out[:300]}")
        return False


def ensure_git_config(repo_path: str):
    """Ensure git user config exists for the repo."""
    repo = Path(repo_path)
    if not (repo / ".git").exists():
        return
    out, _ = run("git config user.name", timeout=5, cwd=str(repo))
    if not out.strip():
        run('git config user.name "Hermes Swarm Loop"', timeout=5, cwd=str(repo))
        run('git config user.email "swarm@hermes.loop"', timeout=5, cwd=str(repo))


def push_framework(message: str = ""):
    """Convenience: push the hermes-swarm-loop framework repo."""
    here = Path(__file__).resolve().parent.parent
    ensure_git_config(str(here))
    return git_push_repo(str(here), message=message)


def push_project(project_dir: str = "/opt/email-platform", message: str = ""):
    """Convenience: push the project repo."""
    ensure_git_config(project_dir)
    return git_push_repo(project_dir, message=message)
