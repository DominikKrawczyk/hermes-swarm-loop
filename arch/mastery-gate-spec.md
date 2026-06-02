# Mastery Gate — 7-Dimension Scoring Specification

## Overview

The Mastery Gate evaluates whether a phase or point is ready to advance by
scoring it across 7 dimensions. It produces one of four verdicts that determine
the next action in the swarm pipeline.

```
┌─────────────────────────────────────────────────────────────┐
│                   MASTERY GATE                                │
│                                                              │
│  Input: MasteryScore (7 dimensions [0.0, 1.0])               │
│         + Optional metadata                                  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  1. Completeness  ─── 0.20 weight                    │     │
│  │  2. Correctness   ─── 0.20 weight                    │     │
│  │  3. Coverage      ─── 0.15 weight                    │     │
│  │  4. Consistency   ─── 0.15 weight                    │     │
│  │  5. Clarity       ─── 0.10 weight                    │     │
│  │  6. Confidence    ─── 0.10 weight                    │     │
│  │  7. Novelty       ─── 0.10 weight                    │     │
│  └─────────────────────────────────────────────────────┘     │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐     │
│  │                VERDICT DETERMINATION                  │     │
│  │                                                      │     │
│  │  PASS ◄─── score ≥ 0.85 AND all dims ≥ 0.70        │     │
│  │                                                      │     │
│  │  CROSS-CHECK ◄─── score ≥ 0.70 AND all dims ≥ 0.50 │     │
│  │                                                      │     │
│  │  REVIEW ◄─── score ≥ 0.50 AND all dims ≥ 0.30      │     │
│  │                                                      │     │
│  │  BLOCK ◄─── score < 0.50 OR any dim < 0.30         │     │
│  └─────────────────────────────────────────────────────┘     │
│                           │                                  │
│                           ▼                                  │
│              ┌─────────────────────────┐                     │
│              │  GateResult             │                     │
│              │  - verdict (enum)       │                     │
│              │  - score (float)        │                     │
│              │  - dimension_scores     │                     │
│              │  - reasons (list[str])  │                     │
│              │  - metadata (dict)      │                     │
│              └─────────────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Dimension Definitions

### 1. Completeness (weight: 0.20)
How fully the feature/component is implemented.
- 1.0: All requirements met, no missing pieces
- 0.7: Core functionality present, minor gaps
- 0.4: Key features missing
- 0.0: Nothing implemented

### 2. Correctness (weight: 0.20)
Freedom from bugs, errors, and logical flaws.
- 1.0: Verified correct, passes all tests
- 0.7: Minor bugs found, nothing critical
- 0.4: Significant correctness issues
- 0.0: Fundamentally broken

### 3. Coverage (weight: 0.15)
Breadth and depth of test coverage and edge-case handling.
- 1.0: Comprehensive tests, edge cases covered
- 0.7: Core paths tested, some gaps
- 0.4: Minimal coverage
- 0.0: No tests

### 4. Consistency (weight: 0.15)
Adherence to conventions, patterns, and architectural consistency.
- 1.0: Fully consistent with project patterns
- 0.7: Minor inconsistencies
- 0.4: Notable deviations
- 0.0: No coherent pattern

### 5. Clarity (weight: 0.10)
Readability, documentation, and code comprehensibility.
- 1.0: Well-documented, clear names, obvious intent
- 0.7: Adequate documentation
- 0.4: Hard to follow, sparse docs
- 0.0: Obfuscated, undocumented

### 6. Confidence (weight: 0.10)
How certain we are about the assessment itself.
- 1.0: Thoroughly analyzed, high certainty
- 0.7: Reasonably confident
- 0.4: Uncertain, needs more analysis
- 0.0: Guesswork

### 7. Novelty (weight: 0.10)
Innovation and creativity of the solution.
- 1.0: Novel approach, significant innovation
- 0.7: Solid solution with some new ideas
- 0.4: Standard implementation
- 0.0: Copy-paste, no original thought

---

## Weighted Score Calculation

```python
weighted_score = sum(score[dim] * weight[dim] for dim in DIMENSIONS)
                / sum(weight[dim] for dim in DIMENSIONS)
```

With default weights:
```
weighted = (completeness × 0.20)
         + (correctness    × 0.20)
         + (coverage       × 0.15)
         + (consistency    × 0.15)
         + (clarity        × 0.10)
         + (confidence     × 0.10)
         + (novelty        × 0.10)
```

Weights are normalized so: sum(weights) = 1.0

---

## Verdict Paths

### PASS
```
Conditions:
  weighted_score >= pass_threshold (default: 0.85)
  AND all dimension scores >= min_dimension_pass (default: 0.70)

Action:
  Point/phase advances to next stage automatically.
  No human review needed.
```

### CROSS-CHECK
```
Conditions:
  weighted_score >= cross_check_threshold (default: 0.70)
  AND all dimension scores >= min_dimension_cross_check (default: 0.50)

Action:
  Automatic advancement with a note to cross-check.
  A second opinion is recommended but not blocking.
  Common when one dimension is slightly below PASS threshold.
```

### REVIEW
```
Conditions:
  weighted_score >= review_threshold (default: 0.50)
  AND all dimension scores >= min_dimension_review (default: 0.30)

Action:
  Blocked until human reviews the output.
  Needs manual approval before proceeding.
  Common when multiple dimensions need improvement.
```

### BLOCK
```
Conditions:
  weighted_score < review_threshold (default: 0.50)
  OR any dimension score < min_dimension_review (default: 0.30)

Action:
  Blocked with no advancement.
  Requires re-execution of the point/phase.
  Common when fundamental issues exist.
```

---

## API Reference

### MasteryScore

```python
class MasteryScore:
    DIMENSIONS = [
        "completeness", "correctness", "coverage",
        "consistency", "clarity", "confidence", "novelty",
    ]

    def __init__(self, scores: dict[str, float] | None = None):
        """Create with optional dimension scores (all others default to 0.0)."""

    def get_weighted_score(self, weights: dict[str, float] | None = None) -> float:
        """Compute weighted average. Uses default weights if none provided."""

    def get_min_score(self) -> float:
        """Return the minimum dimension score."""

    def get_weakest_dimension(self) -> tuple[str, float]:
        """Return (name, score) of the lowest dimension."""

    def set_dimension(self, dimension: str, score: float):
        """Set a single dimension score (clamped to [0, 1])."""

    def to_dict(self) -> dict[str, float]:
        """Return all dimension scores as a flat dict."""
```

### MasteryGate

```python
class MasteryGate:
    def __init__(self, weights=None, pass_threshold=0.85,
                 cross_check_threshold=0.70, review_threshold=0.50,
                 min_dimension_pass=0.70,
                 min_dimension_cross_check=0.50,
                 min_dimension_review=0.30):
        ...

    def evaluate(self, scores: MasteryScore,
                 metadata: dict | None = None) -> GateResult:
        """Evaluate scores and return a verdict with reasons."""

    def evaluate_raw(self, **dimension_scores) -> GateResult:
        """Convenience: pass dimension scores as keyword args."""

    def update_weights(self, weights: dict[str, float]):
        """Update dimension weights (auto-normalized to sum 1.0)."""
```

### Verdict

```python
class Verdict(str, Enum):
    PASS = "PASS"               # Auto-advance
    CROSS_CHECK = "CROSS-CHECK"  # Advance with note
    REVIEW = "REVIEW"           # Human review needed
    BLOCK = "BLOCK"             # Re-execute needed
```

### GateResult

```python
class GateResult:
    verdict: Verdict       # The determined verdict
    score: float           # Weighted score
    dimension_scores: dict # Per-dimension scores
    reasons: list[str]     # Human-readable reasons
    metadata: dict         # Optional metadata

    def to_dict(self) -> dict:
        """Serialize to plain dict."""

    @classmethod
    def from_dict(cls, d: dict) -> "GateResult":
        """Deserialize from dict."""
```

---

## Configuration

Default thresholds can be overridden via constructor:

```python
# Stricter gate
strict_gate = MasteryGate(
    pass_threshold=0.95,
    cross_check_threshold=0.85,
    review_threshold=0.70,
)

# Relaxed gate for early phases
relaxed_gate = MasteryGate(
    pass_threshold=0.70,
    min_dimension_pass=0.50,
)
```

Custom dimension weights:

```python
# Emphasize completeness and correctness
custom_gate = MasteryGate(weights={
    "completeness": 0.30,
    "correctness": 0.30,
    "coverage": 0.10,
    "consistency": 0.10,
    "clarity": 0.05,
    "confidence": 0.05,
    "novelty": 0.10,
})
```

---

## Event Logging

Every gate evaluation should be logged to the event log for audit:

```json
{
  "event": "gate_evaluation",
  "payload": {
    "verdict": "PASS",
    "score": 0.92,
    "dimension_scores": {
      "completeness": 0.95,
      "correctness": 0.90,
      "coverage": 0.92,
      "consistency": 0.93,
      "clarity": 0.91,
      "confidence": 0.88,
      "novelty": 0.85
    },
    "reasons": [
      "Weighted score 0.9200 >= 0.85",
      "All dimensions >= 0.70"
    ]
  }
}
```
