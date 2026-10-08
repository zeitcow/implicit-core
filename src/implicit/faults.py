from .learning import LearningState
from .models import Execution, ExperienceFault, LogicalExperience, VerificationResult
from .serialization import content_hash


class FaultExtractor:
    def extract(
        self,
        experience: LogicalExperience,
        execution: Execution,
        verification: VerificationResult,
        state: LearningState,
        *,
        observation_id: str,
    ) -> tuple[ExperienceFault, ...]:
        if verification.passed:
            return ()
        failed = [c for c in verification.components if not c.passed]
        components = [(c.name, c.stage, c.score, c.evidence) for c in failed]
        if not components:
            components = [("overall_reward", "unresolved", verification.reward, ())]
        result = []
        region = experience.address.region
        policy_ref = execution.outcome.get("policy_reference")
        policies = (*region.policies, policy_ref) if isinstance(policy_ref, str) else region.policies
        for name, stage, score, evidence in components:
            hierarchy = (region.domain, region.name, stage, name)
            repeats = 1 + state.hierarchy_counts.get(
                hierarchy, sum(f.hierarchy == hierarchy for f in state.faults)
            )
            result.append(
                ExperienceFault(
                    content_hash((observation_id, hierarchy)),
                    experience.address,
                    name,
                    stage,
                    min(1.0, max(0.05, 1.0 - score)),
                    (0.75 if any("inferred" in e for e in evidence) else 1.0)
                    if stage != "unresolved"
                    else 0.5,
                    (0.25 if any("inferred" in e for e in evidence) else 0.0)
                    if stage != "unresolved"
                    else 0.5,
                    tuple(dict.fromkeys(action.tool for action in execution.actions)),
                    policies,
                    experience.tags,
                    experience.features,
                    execution.cost_usd,
                    (observation_id, verification.authority, *execution.provenance, *evidence),
                    hierarchy,
                    repeats,
                    repeats >= 3,
                )
            )
        return tuple(result)
