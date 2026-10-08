"""Core selection preserves the external universe's order; no adaptive allocation."""

from .learning import LearningState
from .models import AllocationDecision, CandidateExperience, ProbeResult


class OrderedSearch:
    def rank(self, probes: tuple[ProbeResult, ...], state: LearningState) -> tuple[CandidateExperience, ...]:
        return tuple(CandidateExperience(p, 1.0, ("external proposal order",)) for p in probes)


class OrderedSelector:
    def select(
        self, candidates: tuple[CandidateExperience, ...], state: LearningState, *, seed: int
    ) -> AllocationDecision:
        if not candidates:
            raise LookupError("no proposed experience")
        return AllocationDecision(
            candidates[0], "explore", "external proposal order", (), tuple(state.observations)
        )
