# Workspace Manager Specification

## Overview

The Workspace Manager provides three kinds of workspaces for agent tasks.
Each workspace type offers different isolation, persistence, and lifecycle
properties suited to different stages of the build pipeline.

```
┌─────────────────────────────────────────────────────────────┐
│                  WORKSPACE MANAGER                            │
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │   scratch   │    │     dir     │    │  worktree   │       │
│  │             │    │             │    │             │       │
│  │ Ephemeral   │    │  Persistent │    │  Git branch │       │
│  │ tmpdir      │    │  directory  │    │  worktree   │       │
│  │             │    │             │    │             │       │
│  │ GC on done  │    │  No GC      │    │  No GC      │       │
│  │ Strong iso  │    │  Shared     │    │  Branch iso │       │
│  └─────────────┘    └─────────────┘    └─────────────┘       │
│                                                              │
│              Default: scratch                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration (`configs/workspace.yaml`)

```yaml
workspaces:
  scratch:
    description: "Fresh tmp directory — worker's exclusive space"
    gc_on_complete: true
    isolation: strong
    persistence: false

  dir:
    description: "Shared persistent directory — multiple workers read/write"
    gc_on_complete: false
    isolation: shared
    persistence: true

  worktree:
    description: "Git worktree — branch-per-task development"
    gc_on_complete: false
    isolation: branch
    persistence: true
    auto_commit: true

default_workspace: scratch
```

---

## Workspace Types

### Scratch (default)

**Use case:** Short-lived agent tasks that produce temporary output.

```
Properties:
  - Created:   tempfile.mkdtemp()
  - Path:      /tmp/swarm_{task_id}_XXXXXX
  - Lifecycle: Available during task → destroyed on complete/fail
  - GC:        Automatic — shutil.rmtree() on destroy()
  - Isolation: Strong — each task gets its own directory
  - Persistence: None — destroyed when task ends

Lifecycle:
  create(task_id, "scratch") → Workspace(path, is_ready=True)
  ... agent works in path ...
  destroy(workspace) → files cleaned up
```

### Dir

**Use case:** Long-lived shared state, multi-worker collaboration.

```
Properties:
  - Created:   os.makedirs(shared_dir / task_id)
  - Path:      {base_dir}/shared/{task_id} or custom path
  - Lifecycle: Manual — persists across task boundaries
  - GC:        None — files remain after task completes
  - Isolation: Shared — multiple workers can read/write
  - Persistence: Yes — data survives task end

Lifecycle:
  create(task_id, "dir", workspace_path="/persistent/data") → Workspace
  ... multiple workers cooperate ...
  destroy(workspace) → no-op (files preserved)
```

### Worktree

**Use case:** Code changes with version history, branch-per-task.

```
Properties:
  - Created:   git worktree add
  - Path:      {base_dir}/worktrees/{task_id}
  - Branch:    wt/{task_id}
  - Lifecycle: Task duration + manual cleanup
  - GC:        git worktree remove on destroy()
  - Isolation: Branch — each task gets its own branch
  - Persistence: Yes — git history persists
  - Auto-commit: Optional automatic commits

Requirements:
  - Must be inside a git repository
  - Repository must exist at base_dir

Lifecycle:
  create(task_id, "worktree") → Workspace
    1. Create branch wt/{task_id} if not exists
    2. git worktree add {path} wt/{task_id}
    3. Return ready workspace
  ... agent makes changes and commits ...
  destroy(workspace)
    1. git worktree remove {path}
    2. Branch remains for reference
```

---

## API Reference

### Workspace

```python
@dataclass
class Workspace:
    kind: str       # "scratch" | "dir" | "worktree"
    path: str       # Absolute path to workspace directory
    task_id: str    # Associated task ID
    is_ready: bool  # Whether the workspace is ready for use
```

### WorkspaceManager

```python
class WorkspaceManager:
    def __init__(self, base_dir: str, git_repo: str | None = None):
        """Initialize with base directory for workspaces."""

    def create(self, task_id: str, kind: str = "scratch",
               workspace_path: str | None = None) -> Workspace:
        """Create a workspace of the given kind for the task.
        
        Args:
            task_id: Unique identifier for the task
            kind: "scratch", "dir", or "worktree"
            workspace_path: Custom path (dir kind only)
        
        Returns:
            Workspace dataclass with path, kind, and readiness
        """

    def destroy(self, workspace: Workspace):
        """Clean up the workspace.
        
        For scratch: removes temp directory
        For worktree: removes git worktree
        For dir: no-op (files preserved)
        """

    def resolve_path(self, workspace: Workspace, *parts: str) -> str:
        """Resolve a relative path within the workspace."""
```

---

## Thread Safety

WorkspaceManager operations are **not** thread-safe by default. Concurrent
`create()` calls may race on directory creation or git branch creation.
Wrap calls in external locks when used from multiple threads.

---

## Example Usage

```python
from engine.workspace_manager import WorkspaceManager

wm = WorkspaceManager("/opt/hermes-swarm-loop")

# Create a scratch workspace for a short audit task
ws = wm.create("audit_001", "scratch")
print(f"Working in: {ws.path}")
# ... run audit agent in ws.path ...
wm.destroy(ws)  # auto-cleaned

# Create a persistent shared workspace
ws = wm.create("shared_data", "dir", 
               workspace_path="/opt/hermes-swarm-loop/shared/analysis")
# ... multiple workers access ws.path ...
wm.destroy(ws)  # no-op, files preserved

# Create a git worktree for code changes
ws = wm.create("feature_xyz", "worktree")
# ... agent modifies code and commits ...
# git add, git commit in ws.path
wm.destroy(ws)  # removes worktree, branch preserved
```
