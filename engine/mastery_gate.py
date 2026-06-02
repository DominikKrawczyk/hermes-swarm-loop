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
    def __init__(self, prd_areas=None):
        self.prd_areas = prd_areas or ["arch","setup","code","test","security","scaling","ux"]
    def evaluate(self, agent_scores):
        if not agent_scores: raise ValueError("No agent scores")
        avg = ScoreCard(); n = len(agent_scores)
        for dim in DIMENSIONS:
            setattr(avg, dim, sum(getattr(s,dim) for s in agent_scores)/n)
        return avg
    def check_diversification(self, s):
        g = []
        if s.diversity < 0.5: g.append("diversity too concentrated")
        if s.correctness < 0.5: g.append("correctness below threshold")
        if s.safety < 0.5: g.append("safety concerns")
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
