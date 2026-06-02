"""Tests for WorkspaceManager — scratch/dir/worktree lifecycle.

These tests verify the three workspace kinds and their lifecycle methods.
Scratch workspaces are fully tested (setup, teardown, GC).
Dir workspaces verify path creation and that teardown is a no-op.
Worktree tests verify git integration (when a repo is available).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from engine.gate_11 import Gate11Verifier
from engine.workspace_manager import (
    Workspace,
    WorkspaceError,
    WorkspaceKind,
    WorkspaceManager,
)

# ═══════════════════════════════════════════════════════════════════
# WorkspaceManager — Validation / Parsing
# ═══════════════════════════════════════════════════════════════════

class TestWorkspaceParsing:
    def test_resolve_kind_scratch(self):
        wm = WorkspaceManager()
        assert wm.resolve_kind_from_token("scratch") == WorkspaceKind.SCRATCH
        assert wm.resolve_kind_from_token("SCRATCH") == WorkspaceKind.SCRATCH

    def test_resolve_kind_dir(self):
        wm = WorkspaceManager()
        assert wm.resolve_kind_from_token("dir:/opt/data") == WorkspaceKind.DIR

    def test_resolve_kind_worktree(self):
        wm = WorkspaceManager()
        assert wm.resolve_kind_from_token("worktree") == WorkspaceKind.WORKTREE

    def test_resolve_kind_invalid_raises(self):
        wm = WorkspaceManager()
        from pytest import raises
        with raises(WorkspaceError):
            wm.resolve_kind_from_token("bogus")

    def test_resolve_path_dir(self):
        wm = WorkspaceManager()
        p = wm.resolve_path_from_token("dir:/opt/workspace")
        assert p == Path("/opt/workspace")

    def test_resolve_path_scratch(self):
        wm = WorkspaceManager()
        assert wm.resolve_path_from_token("scratch") is None

    def test_resolve_path_invalid_relative_raises(self):
        wm = WorkspaceManager()
        from pytest import raises
        with raises(WorkspaceError, match="absolute"):
            wm.resolve_path_from_token("dir:relative/path")


# ═══════════════════════════════════════════════════════════════════
# WorkspaceManager — Scratch
# ═══════════════════════════════════════════════════════════════════

class TestWorkspaceScratch:
    def test_scratch_creates_directory(self):
        wm = WorkspaceManager(workspace_root="/tmp/hermes-test-scratch")
        ws = wm.setup("scratch", task_id="t_scratch_01")
        assert ws.path.exists()
        assert ws.path.is_dir()
        assert ws.kind == WorkspaceKind.SCRATCH
        wm.teardown(ws)

    def test_scratch_label_default(self):
        wm = WorkspaceManager(workspace_root="/tmp/hermes-test-label")
        ws = wm.setup("scratch", task_id="t_label")
        assert ws.label == "t_label"
        wm.teardown(ws)

    def test_scratch_teardown_removes_directory(self):
        wm = WorkspaceManager(workspace_root="/tmp/hermes-test-teardown")
        ws = wm.setup("scratch", task_id="t_remove")
        path = ws.path
        assert path.exists()
        wm.teardown(ws, cleanup=True)
        assert not path.exists()

    def test_scratch_teardown_no_cleanup_keeps_dir(self):
        wm = WorkspaceManager(workspace_root="/tmp/hermes-test-noclean")
        ws = wm.setup("scratch", task_id="t_noclean")
        path = ws.path
        assert path.exists()
        wm.teardown(ws, cleanup=False)
        assert path.exists()
        # Clean up manually
        import shutil
        shutil.rmtree(path, ignore_errors=True)

    def test_scratch_teardown_twice_does_not_error(self):
        wm = WorkspaceManager(workspace_root="/tmp/hermes-test-double")
        ws = wm.setup("scratch", task_id="t_double")
        wm.teardown(ws)
        # Second teardown should be a no-op
        wm.teardown(ws)

    def test_scratch_multiple_isolation(self):
        wm = WorkspaceManager(workspace_root="/tmp/hermes-test-multi")
        ws1 = wm.setup("scratch", task_id="t_a")
        ws2 = wm.setup("scratch", task_id="t_b")
        assert ws1.path != ws2.path
        assert ws1.path.exists()
        assert ws2.path.exists()
        wm.teardown(ws1)
        wm.teardown(ws2)

    def test_current_task_workspace_found(self):
        wm = WorkspaceManager(workspace_root="/tmp/hermes-test-find")
        ws = wm.setup("scratch", task_id="t_findme")
        found = wm.current_task_workspace("t_findme")
        assert found is not None
        assert found.path == ws.path
        wm.teardown(ws)

    def test_current_task_workspace_not_found(self):
        wm = WorkspaceManager()
        assert wm.current_task_workspace("nonexistent") is None

    def test_list_active(self):
        wm = WorkspaceManager(workspace_root="/tmp/hermes-test-active")
        ws1 = wm.setup("scratch", task_id="t_active1")
        ws2 = wm.setup("scratch", task_id="t_active2")
        active = wm.list_active()
        assert len(active) == 2
        wm.teardown(ws1)
        wm.teardown(ws2)


# ═══════════════════════════════════════════════════════════════════
# WorkspaceManager — Dir
# ═══════════════════════════════════════════════════════════════════

class TestWorkspaceDir:
    def test_dir_creates_path(self, tmp_path: Path):
        wm = WorkspaceManager()
        target = tmp_path / "shared"
        ws = wm.setup("dir", dir_path=str(target))
        assert ws.path.exists()
        assert ws.path.is_dir()
        assert ws.kind == WorkspaceKind.DIR

    def test_dir_creates_parents(self, tmp_path: Path):
        wm = WorkspaceManager()
        deep = tmp_path / "a" / "b" / "c" / "workspace"
        ws = wm.setup("dir", dir_path=str(deep))
        assert ws.path.exists()
        assert ws.path.parent.parent.parent.exists()

    def test_dir_missing_path_raises(self):
        wm = WorkspaceManager()
        from pytest import raises
        with raises(WorkspaceError, match="requires a --dir-path"):
            wm.setup("dir")

    def test_dir_teardown_noop(self, tmp_path: Path):
        wm = WorkspaceManager()
        target = tmp_path / "persistent"
        ws = wm.setup("dir", dir_path=str(target))
        assert ws.path.exists()
        wm.teardown(ws)  # Should NOT remove dir workspaces
        assert ws.path.exists()


# ═══════════════════════════════════════════════════════════════════
# WorkspaceManager — Worktree
# ═══════════════════════════════════════════════════════════════════

class TestWorkspaceWorktree:
    def test_worktree_no_repo_raises(self):
        wm = WorkspaceManager()
        from pytest import raises
        with raises(WorkspaceError, match="requires a main_repo"):
            wm.setup("worktree")

    def test_worktree_missing_repo_path_raises(self, tmp_path: Path):
        fake_repo = tmp_path / "not-a-repo"
        wm = WorkspaceManager(main_repo=str(fake_repo))
        from pytest import raises
        with raises(WorkspaceError, match="Not a Git repository"):
            wm.setup("worktree", task_id="t_worktree")


# ═══════════════════════════════════════════════════════════════════
# Workspace dataclass
# ═══════════════════════════════════════════════════════════════════

class TestWorkspaceDataclass:
    def test_is_git_worktree_false_for_scratch(self, tmp_path: Path):
        ws = Workspace(kind=WorkspaceKind.SCRATCH, path=tmp_path)
        assert ws.is_git_worktree is False

    def test_is_ready_true(self, tmp_path: Path):
        d = tmp_path / "ready_dir"
        d.mkdir()
        (d / "file.txt").write_text("hello")
        ws = Workspace(kind=WorkspaceKind.DIR, path=d)
        assert ws.is_ready is True

    def test_is_ready_true_when_empty(self, tmp_path: Path):
        d = tmp_path / "empty_dir"
        d.mkdir()
        ws = Workspace(kind=WorkspaceKind.DIR, path=d)
        assert ws.is_ready is True  # directory exists

    def test_is_ready_false_when_nonexistent(self, tmp_path: Path):
        d = tmp_path / "does_not_exist"
        ws = Workspace(kind=WorkspaceKind.DIR, path=d)
        assert ws.is_ready is False

    def test_workspace_repr(self):
        ws = Workspace(kind=WorkspaceKind.SCRATCH, path=Path("/tmp/x"))
        r = repr(ws)
        assert "scratch" in r
        assert "/tmp/x" in r


# ═══════════════════════════════════════════════════════════════════
# Gate11Verifier — smoke test
# ═══════════════════════════════════════════════════════════════════

class TestGate11Smoke:
    def test_verify_eleven_passes(self):
        v = Gate11Verifier()
        handoffs = [
            {"worker_id": f"a{i:02d}", "summary": "done", "point": "setup",
             "phase": "dev", "status": "done"}
            for i in range(11)
        ]
        result = v.verify(handoffs)
        assert result.passed is True
        assert result.all_done is True

    def test_verify_ten_fails(self):
        v = Gate11Verifier()
        handoffs = [
            {"worker_id": f"a{i:02d}", "summary": "done", "point": "setup",
             "phase": "dev", "status": "done"}
            for i in range(10)
        ]
        result = v.verify(handoffs)
        assert result.passed is False

    def test_to_dict(self):
        v = Gate11Verifier()
        handoffs = [{"worker_id": "a01", "summary": "done",
                      "point": "setup", "phase": "dev", "status": "done"}
                    for _ in range(11)]
        result = v.verify(handoffs)
        d = result.to_dict()
        assert d["passed"] is True
        assert d["total_agents"] == 11

    def test_validate_handoff_type_mismatch(self):
        """validate_handoff catches wrong-type fields."""
        v = Gate11Verifier()
        # 'summary' should be str; pass int instead
        result = v.validate_handoff({
            "summary": 42, "worker_id": "w01", "point": "x", "phase": "y",
        }, "w01")
        assert not result.valid
        assert any("wrong type" in e for e in result.errors)

    def test_verify_all_done_false_when_some_not_done(self):
        """11 handoffs but not all 'done' -> passed=False."""
        v = Gate11Verifier()
        handoffs = [
            {"worker_id": f"a{i:02d}", "summary": "done",
             "point": "setup", "phase": "dev", "status": "done" if i < 10 else "running"}
            for i in range(11)
        ]
        result = v.verify(handoffs)
        assert result.passed is False
        assert result.all_done is False

    def test_verify_from_json_valid(self):
        v = Gate11Verifier()
        raw = json.dumps([
            {"worker_id": f"a{i:02d}", "summary": "done",
             "point": "setup", "phase": "dev", "status": "done"}
            for i in range(11)
        ])
        result = v.verify_from_json(raw)
        assert result.passed is True

    def test_verify_from_json_invalid_json(self):
        v = Gate11Verifier()
        result = v.verify_from_json("not json")
        assert result.passed is False
        assert any("Invalid JSON" in e for e in result.errors)

    def test_verify_from_json_not_list(self):
        v = Gate11Verifier()
        result = v.verify_from_json('{"not": "a list"}')
        assert result.passed is False
        assert any("JSON array" in e for e in result.errors)

    def test_verify_not_enough_agents(self):
        v = Gate11Verifier()
        result = v.verify([])
        assert result.passed is False
        assert any("Not enough agents" in e for e in result.errors)

    def test_handoff_validation_without_missing_worker(self):
        """Missing worker_id -> defaults to 'unknown'."""
        v = Gate11Verifier()
        h = {"summary": "done", "point": "p", "phase": "ph"}
        v_result = v.validate_handoff(h, "unknown")
        assert not v_result.valid
        assert any("worker_id" in e for e in v_result.errors)


# ═══════════════════════════════════════════════════════════════════
# WorkspaceManager — Worktree with real git repo
# ═══════════════════════════════════════════════════════════════════

class TestWorkspaceWorktreeIntegration:
    """Worktree tests using a real tmp_path git repo."""

    def _init_repo(self, path: Path, branch: str = "main") -> Path:
        """Initialize a git repo at *path* with one commit on *branch*."""
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-b", branch], cwd=str(path),
                       capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"],
                       cwd=str(path), capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"],
                       cwd=str(path), capture_output=True, check=True)
        (path / "README.md").write_text("# Test Repo")
        subprocess.run(["git", "add", "."], cwd=str(path),
                       capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(path),
                       capture_output=True, check=True)
        return path

    def test_worktree_create_and_teardown(self, tmp_path: Path):
        """Create a git repo, add a worktree, then tear it down."""
        repo = self._init_repo(tmp_path / "main-repo")
        # Create the branch first
        subprocess.run(["git", "branch", "feature/test-branch"],
                       cwd=str(repo), capture_output=True, check=True)

        wm = WorkspaceManager(main_repo=str(repo))
        ws = wm.setup("worktree", task_id="t_worktree_integration",
                       branch="feature/test-branch")
        assert ws.path.exists()
        assert ws.kind == WorkspaceKind.WORKTREE
        assert ws.branch == "feature/test-branch"
        assert (ws.path / "README.md").exists()

        # Teardown removes the worktree
        wm.teardown(ws, cleanup=True)
        assert not ws.path.exists()

    def test_worktree_existing_path_does_not_recreate(self, tmp_path: Path):
        """If the worktree path already exists, setup does not error."""
        repo = self._init_repo(tmp_path / "repo")
        subprocess.run(["git", "branch", "feature/existing"],
                       cwd=str(repo), capture_output=True, check=True)

        wm = WorkspaceManager(main_repo=str(repo))
        ws = wm.setup("worktree", task_id="t_existing",
                       branch="feature/existing")
        assert ws.path.exists()

        # Setting up again with same branch should not error
        wm2 = WorkspaceManager(main_repo=str(repo))
        ws2 = wm2.setup("worktree", task_id="t_existing_2",
                         branch="feature/existing")
        assert ws2.path.exists()
        wm2.teardown(ws2, cleanup=True)

        # Cleanup first worktree too
        wm.teardown(ws, cleanup=True)
