# YOLO Zones — Configuration and Behavior

## Overview

YOLO (You Only Loop Once) zones control agent approval behavior and parallel
execution limits. Four zones form a progression from maximum safety to
maximum velocity.

```
                  RISK / VELOCITY →
                  
  ┌──────┐     ┌──────┐     ┌────────┐     ┌──────────┐
  │ SAFE │────▶│ TEST │────▶│STAGING │────▶│PRODUCTION│
  │      │     │      │     │        │     │          │
  │  cap: 5    │ cap: 11    │ cap: 33     │ cap: 999 │
  │ auto: No   │ auto: Yes  │ auto: Yes   │ auto: Yes │
  │ valve: On  │ valve: On  │ valve: Off  │ valve: Off│
  │ errs: 3    │ errs: 5    │ errs: 10    │ errs: 999 │
  └──────┘     └──────┘     └────────┘     └──────────┘
       │           │             │               │
       │           │             │               │
  Manual      Semi-auto    Auto-approve    Full YOLO
  approval    approval     all actions      no brakes
```

---

## Zone Definitions

### Safe Zone

**Description:** Minimal risk — each action requires approval.

```yaml
safe:
  auto_approve: false
  max_parallel: 5
  safety_valve_enabled: true
  max_consecutive_errors: 3
```

- Every agent action requires manual approval
- Maximum 5 agents running in parallel
- Safety valve automatically reverts to stricter mode after 3 consecutive errors
- **Use when:** First run, unknown territory, experimental work

### Test Zone

**Description:** Testing — auto-approve routine actions, manual for risky ones.

```yaml
test:
  auto_approve: true
  max_parallel: 11
  safety_valve_enabled: true
  max_consecutive_errors: 5
```

- Routine actions auto-approved (reads, small edits)
- Risky actions flagged for manual review
- Maximum 11 agents running in parallel
- Safety valve engages after 5 consecutive errors
- **Use when:** Standard development, confident but cautious

### Staging Zone

**Description:** Staging — auto-approve all, production-like without consequences.

```yaml
staging:
  auto_approve: true
  max_parallel: 33
  safety_valve_enabled: false
  max_consecutive_errors: 10
```

- All actions auto-approved
- Maximum 33 agents running in parallel
- No safety valve — errors tracked but don't auto-pause
- **Use when:** Pre-production validation, scale testing

### Production Zone

**Description:** Full YOLO — no brakes, maximum velocity, up to 999 agents.

```yaml
production:
  auto_approve: true
  max_parallel: 999
  safety_valve_enabled: false
  max_consecutive_errors: 999
```

- All actions auto-approved
- Maximum 999 agents running in parallel
- No safety valve, no error limiting
- **Use when:** Deploying to production, time-critical fixes, full trust

---

## Safety Valve

The safety valve is an automatic protection mechanism for safe and test zones.

### How It Works

```
                   Consecutive Errors Counter
                              │
                    increment_error() called
                              │
                              ▼
                    counter += 1
                              │
                              ▼
              counter >= max_consecutive_errors?
                    ┌────┴────┐
                   YES        NO
                    │         │
                    ▼         ▼
          safety_valve    Continue
          activated       normally
              │
              ▼
    ┌─────────────────────┐
    │ safety_valve_active │  → admit() returns False
    │ = True              │  → No new agents admitted
    └─────────────────────┘
              │
              ▼
    Manual reset required:
    reset_safety_valve()
              │
              ▼
    counter = 0
    active = False
    Normal operation resumes
```

### Safety Valve Settings by Zone

| Zone | Enabled | Threshold | Auto-reset | Cooldown |
|------|---------|-----------|------------|----------|
| safe | Yes | 3 | No | — |
| test | Yes | 5 | No | — |
| staging | No | — | — | — |
| production | No | — | — | — |

### Global Safety Valve Configuration

```yaml
safety_valve:
  enabled: true
  cooldown_seconds: 300
  auto_reset: false
```

---

## Zone Escalation and De-escalation

### Escalation (increase velocity)

Can be done programmatically or via configuration change:

```python
yolo_machine.set_zone("test")      # safe → test
yolo_machine.set_zone("staging")   # test → staging
yolo_machine.set_zone("production")# staging → production
```

### De-escalation (increase safety)

Occurs automatically when safety valve engages (safe/test zones) or manually:

```python
yolo_machine.set_zone("safe")      # any zone → safe
# Or use the safety valve reset:
yolo_machine.reset_safety_valve()  # returns to safe defaults
```

### Recommended Progression

```
Bootstrap → safe (first cycle)
              ↓ (confidence grows)
            test (standard development)
              ↓ (validation passes)
            staging (pre-production)
              ↓ (ready to ship)
            production (deployment)
```

---

## Admission Control

The YOLOMachine's `admit()` method gates agent entry:

```python
def admit(self, current_runners: int, zone_name: str | None = None) -> bool:
    """Check whether a new runner may be admitted.
    
    Returns False if:
      - Safety valve is active (safe/test zones only)
      - current_runners >= max_parallel for the active zone
    """
```

---

## Event Log

All zone changes and safety valve events are recorded:

| Event Type | When | Payload |
|------------|------|---------|
| `yolo.zone_change` | Zone switch | old_zone, new_zone, max_parallel, auto_approve |
| `yolo.safety_valve_engaged` | Valve triggers | consecutive_errors, threshold |
| `yolo.safety_valve_reset` | Valve cleared | {} |

---

## YOLOMachine API

```python
class YOLOMachine:
    # Canonical zone definitions
    ZONE_CAPS = {
        "safe":       {"max_parallel": 5,   "auto_approve": False},
        "test":       {"max_parallel": 11,  "auto_approve": True},
        "staging":    {"max_parallel": 33,  "auto_approve": True},
        "production": {"max_parallel": 999, "auto_approve": True},
    }
    ERROR_THRESHOLD = 5

    def set_zone(self, zone_name: str) -> YOLOZoneConfig: ...
    def get_zone(self) -> YOLOZoneConfig: ...
    def zone_caps(self) -> dict[str, YOLOZoneConfig]: ...
    def increment_error(self) -> int: ...
    def reset_safety_valve(self) -> bool: ...
    def is_paused(self) -> bool: ...
    def get_error_count(self) -> int: ...
    def get_full_state(self) -> YOLOState: ...
    def admit(self, current_runners: int, zone_name: str | None = None) -> bool: ...
```
