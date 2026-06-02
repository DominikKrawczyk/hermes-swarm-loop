"""
Mastery Gate Engine — Hermes Swarm Loop
7-dimension scoring for quality gates.
"""

from dataclasses import dataclass, field

DIMENSIONS = {
    "correctness": 0.25, "safety": 0.20, "test_coverage": 0.15,
    "consistency": 0.15, "diversity": 0.10, "efficiency": 0.10, "clarity": 0.05,
}

@dataclass
class ScoreCard:
    correctness: float = 0.0
    safety: float = 0.0
    test_coverage: float = 0.0
    consistency: float = 0.0
    diversity: float = 0.0
    efficiency: float = 0.0
    clarity: float = 0.0
    notes: dict = field(default_factory=dict)

    @property
    def weighted_total(self) -> float:
        return sum(getattr(self, dim) * w for dim, w in DIMENSIONS.items())

    @property
    def verdict(self) -> str:
        t = self.weighted_total
        if t >= 0.70: return "PASS"
        if t >= 0.50: return "CROSS-CHECK"
        if t >= 0.30: return "REVIEW"
        return "BLOCK"

    def to_dict(self) -> dict:
        return {"scores": {d: getattr(self,d) for d in DIMENSIONS},
                "weighted_total": round(self.weighted_total, 4),
                "verdict": self.verdict, "notes": self.notes}

class MasteryGate:
    def __init__(self, prd_areas=None, diversification_threshold=0.5):
        self.prd_areas = prd_areas if prd_areas is not None else ['arch','setup','code','test','security','scaling','ux']
        self.diversification_threshold = diversification_threshold
    def evaluate(self, agent_scores):
        if not agent_scores: raise ValueError("No agent scores")
        # Convert plain dicts to ScoreCard instances to prevent silent all-zeros
        _scores = []
        for s in agent_scores:
            if isinstance(s, dict):
                _scores.append(score_from_dict(s))
            elif isinstance(s, ScoreCard):
                _scores.append(s)
            else:
                raise TypeError(f"Expected ScoreCard or dict, got {type(s).__name__}")
        avg = ScoreCard(); n = len(_scores)
        for dim in DIMENSIONS:
            setattr(avg, dim, sum(getattr(s,dim) for s in _scores)/n)
        return avg
    def check_diversification(self, s):
        g = []
        t = self.diversification_threshold
        if s.diversity < t: g.append(f"diversity too concentrated (below {t})")
        if s.correctness < t: g.append(f"correctness below threshold ({t})")
        if s.safety < t: g.append(f"safety concerns (below {t})")
        return g
    def as_dict(self, phase, point, score, agents_used=1, time_seconds=0.0):
        return {"phase":phase,"point":point,"score":score.to_dict(),
                "agents_used":agents_used,"time_seconds":round(time_seconds,2),
                "gaps":self.check_diversification(score)}

def score_from_dict(d):
    s = ScoreCard()
    for dim in DIMENSIONS:
        if dim in d: setattr(s, dim, float(d[dim]))
    if "notes" in d: s.notes = d["notes"]
    return s
