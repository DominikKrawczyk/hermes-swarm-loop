"""Workspace Manager — scratch/dir/worktree lifecycle for kanban workers.

Each Hermes Kanban task is assigned a workspace of one of three kinds:

- **scratch** — A fresh temporary directory created per task. GC'd when the
  task is archived. Yours alone; read/write freely.
- **dir** — A shared persistent directory at a given absolute path. Multiple
  workers may read/write here over time.
- **worktree** — A Git worktree, created from the main repository on a
  feature branch.

Typical usage::

    wm = WorkspaceManager(workspace_root="/tmp")
    env = wm.setup("scratch", task_id="t_abc123")
    assert env.kind == "scratch"
    assert env.path.exists()
    # ... do work ...
    wm.teardown(env)
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class WorkspaceKind(str, Enum):
    """The three workspace flavours supported by the Hermes Swarm Loop."""

    SCRATCH = "scratch"
    DIR = "dir"
    WORKTREE = "worktree"


@dataclass
class Workspace:
    """A resolved workspace ready for a worker to use.

    Attributes:
        kind: Which flavour of workspace.
        path: Absolute path to the workspace directory.
        label: Human-friendly label (e.g. ``"t_abc123"`` or ``"agent-03"``).
        branch: Git branch name, if any (worktree only).
        metadata: Arbitrary extra info the consumer may need.
    """

    kind: WorkspaceKind
    path: Path
    label: str = ""
    branch: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------

    @property
    def is_git_worktree(self) -> bool:
        """True if this workspace is a Git worktree with a valid .git file."""
        return self.kind == WorkspaceKind.WORKTREE and (self.path / ".git").exists()

    @property
    def is_ready(self) -> bool:
        """True if the directory exists (may be empty for scratch workspaces)."""
        return self.path.is_dir()


class WorkspaceError(Exception):
    """Raised when a workspace lifecycle operation fails."""


class WorkspaceManager:
    """Creates, manages, and tears down workspaces of all three kinds.

    Args:
        workspace_root: Base directory for scratch workspaces.
            ``dir:`` and ``worktree`` workspaces ignore this (they have
            explicit paths).
        main_repo: Absolute path to the main Git repo for worktree
            creation.  If ``None``, worktree operations raise an error.
    """

    def __init__(
        self,
        workspace_root: str | Path = "/tmp/hermes-workspaces",
        main_repo: str | Path | None = None,
    ) -> None:
        self._root = Path(workspace_root)
        self._main_repo = Path(main_repo) if main_repo else None
        self._active: dict[str, Workspace] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def setup(
        self,
        kind: str | WorkspaceKind,
        *,
        task_id: str = "",
        dir_path: str | Path | None = None,
        branch: str | None = None,
        label: str = "",
    ) -> Workspace:
        """Create and prepare a workspace for a worker.

        Args:
            kind: One of ``"scratch"``, ``"dir"``, or ``"worktree"``.
            task_id: Task identifier used to name subdirectories.
            dir_path: Required for ``dir`` workspaces; ignored otherwise.
            branch: Git branch name for ``worktree`` workspaces.
            label: Optional human-friendly label.

        Returns:
            A resolved :class:`Workspace`.

        Raises:
            WorkspaceError: On setup failure (path already exists as file,
                repo not found, git error, etc.).
        """
        kind_enum = WorkspaceKind(kind) if isinstance(kind, str) else kind

        if kind_enum == WorkspaceKind.SCRATCH:
            return self._setup_scratch(task_id=task_id, label=label or task_id)
        elif kind_enum == WorkspaceKind.DIR:
            return self._setup_dir(dir_path=dir_path, label=label)
        elif kind_enum == WorkspaceKind.WORKTREE:
            return self._setup_worktree(branch=branch or f"wt/{task_id}", label=label)
        raise WorkspaceError(f"Unknown workspace kind: {kind}")

    def teardown(self, workspace: Workspace, *, cleanup: bool = True) -> None:
        """Tear down a workspace, optionally cleaning up its contents.

        For scratch workspaces, *cleanup* removes the entire directory.
        For dir workspaces, *cleanup* is a no-op (the caller owns the path).
        For worktree workspaces, *cleanup* runs ``git worktree remove`` if
        the worktree still exists in the repo.

        Args:
            workspace: The workspace to tear down.
            cleanup: Whether to actually remove/purge the workspace.
        """
        if workspace.kind == WorkspaceKind.SCRATCH and cleanup:
            self._teardown_scratch(workspace)
        elif workspace.kind == WorkspaceKind.WORKTREE and cleanup:
            self._teardown_worktree(workspace)
        # DIR workspaces are never cleaned up by us.
        self._active.pop(str(workspace.path), None)

    def current_task_workspace(self, task_id: str) -> Workspace | None:
        """Return the active workspace for *task_id*, if any."""
        for ws in self._active.values():
            if ws.label == task_id:
                return ws
        return None

    def list_active(self) -> list[Workspace]:
        """Return a snapshot of all currently-active workspaces."""
        return list(self._active.values())

    # ------------------------------------------------------------------
    # Scratch workspaces
    # ------------------------------------------------------------------

    def _setup_scratch(self, task_id: str, label: str) -> Workspace:
        self._root.mkdir(parents=True, exist_ok=True)
        try:
            path = Path(tempfile.mkdtemp(prefix=f"{task_id}_", dir=str(self._root)))
        except OSError as exc:
            raise WorkspaceError(f"Failed to create scratch workspace: {exc}") from exc

        ws = Workspace(
            kind=WorkspaceKind.SCRATCH,
            path=path.resolve(),
            label=label,
        )
        self._active[str(path)] = ws
        return ws

    @staticmethod
    def _teardown_scratch(workspace: Workspace) -> None:
        if workspace.path.is_dir():
            shutil.rmtree(workspace.path, ignore_errors=True)

    # ------------------------------------------------------------------
    # Dir workspaces
    # ------------------------------------------------------------------

    @staticmethod
    def _setup_dir(
        dir_path: str | Path | None,
        label: str,
    ) -> Workspace:
        if not dir_path:
            raise WorkspaceError("dir workspace requires a --dir-path argument")
        path = Path(dir_path).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return Workspace(
            kind=WorkspaceKind.DIR,
            path=path,
            label=label or str(path),
        )

    # ------------------------------------------------------------------
    # Git worktree workspaces
    # ------------------------------------------------------------------

    def _setup_worktree(self, branch: str, label: str) -> Workspace:
        if self._main_repo is None:
            raise WorkspaceError(
                "Worktree workspaces requires a main_repo path. "
                "Pass WorkspaceManager(main_repo='/path/to/repo')"
            )
        repo = self._main_repo.resolve()
        if not (repo / ".git").exists():
            raise WorkspaceError(f"Not a Git repository: {repo}")

        # Determine the worktree path: <main_repo>/../worktrees/<branch>/
        worktree_dir = repo.parent / "worktrees" / branch
        worktree_dir = worktree_dir.resolve()

        if worktree_dir.is_dir():
            # Already exists — verify it's valid.
            if not (worktree_dir / ".git").exists():
                raise WorkspaceError(
                    f"Worktree path {worktree_dir} exists but has no .git marker. "
                    "Remove it manually and retry."
                )
        else:
            self._run_git(repo, "worktree", "add", str(worktree_dir), branch)

        ws = Workspace(
            kind=WorkspaceKind.WORKTREE,
            path=worktree_dir,
            label=label,
            branch=branch,
            metadata={"repo": str(repo)},
        )
        self._active[str(worktree_dir)] = ws
        return ws

    def _teardown_worktree(self, workspace: Workspace) -> None:
        repo_raw = workspace.metadata.get("repo", self._main_repo)
        repo_path = Path(str(repo_raw)) if repo_raw else None
        if repo_path and repo_path.exists():
            try:
                self._run_git(
                    Path(repo_path),
                    "worktree",
                    "remove",
                    str(workspace.path),
                )
            except WorkspaceError:
                # Worktree may have been removed already
                pass
        if workspace.path.is_dir():
            shutil.rmtree(workspace.path, ignore_errors=True)

    # ------------------------------------------------------------------
    # Utils
    # ------------------------------------------------------------------

    @staticmethod
    def _run_git(repo: Path, *args: str) -> str:
        """Run *args* as a git command in *repo*.

        Returns:
            The command's stdout as a decoded string.

        Raises:
            WorkspaceError: If the command fails.
        """
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=str(repo),
                capture_output=True,
                text=True,
                timeout=60,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip()
            raise WorkspaceError(
                f"git {' '.join(args)!r} failed (exit {exc.returncode}): {stderr}"
            ) from exc
        except FileNotFoundError as exc:
            raise WorkspaceError("git executable not found on PATH") from exc

    def resolve_kind_from_token(self, token: str) -> WorkspaceKind:
        """Parse a workspace kind token like ``"scratch"`` or ``"dir:/path"``.

        Args:
            token: Either a bare kind (``"scratch"``, ``"worktree"``) or
                ``"dir:<absolute_path>"``.

        Returns:
            The resolved :class:`WorkspaceKind`.

        Raises:
            WorkspaceError: If the token is malformed.
        """
        if token.startswith("dir:"):
            return WorkspaceKind.DIR
        try:
            return WorkspaceKind(token.lower())
        except ValueError:
            raise WorkspaceError(
                f"Invalid workspace kind token: {token!r}. "
                f"Expected 'scratch', 'dir:<path>', or 'worktree'."
            ) from None

    def resolve_path_from_token(self, token: str) -> Path | None:
        """Extract an explicit path from a kind token, if present.

        ``"scratch"`` and ``"worktree"`` return ``None``.
        ``"dir:/opt/data"`` returns ``Path("/opt/data")``.
        """
        if token.startswith("dir:"):
            path_str = token[len("dir:"):]
            if not path_str.startswith("/"):
                raise WorkspaceError(
                    f"dir workspace path must be absolute: {token!r}"
                )
            return Path(path_str)
        return None
