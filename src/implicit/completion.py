"""Two-phase completion: execution is prepared; verification durably terminalizes it.

Recovery verifies a saved execution without invoking native execution again. The
caller must rebind an evaluator against the same environment/source identity.
"""

from __future__ import annotations

from typing import Any, Callable

from .models import Event, Execution, LogicalExperience, VerificationResult
from .privacy import safe
from .recovery import restore
from .serialization import content_hash, json_value
from .storage import EventStore

POLICY = {
    "version": 1,
    "terminal": "one durable append containing prepared execution and verified result",
    "recovery": "verification only; native execution replay prohibited",
    "provider": "at most one identical transient retry before terminal commit",
    "ambiguity": "retain prepared state; fail closed",
}


class CompletionTransaction:
    def __init__(self, store: EventStore, identity: str, provenance: dict[str, Any] | None = None) -> None:
        self.store, self.identity = store, identity
        self.manifest = safe({"completion_policy": POLICY, "provenance": provenance or {}})

    def prepare(self, experience: LogicalExperience, execution: Execution) -> None:
        with self.store.lease(self.identity):
            # A durable prepared execution is never replaced, even after failure.
            self.store.create_session(self.identity, self.manifest)
            payload = safe(json_value({"experience": experience, "execution": execution}))
            payload["sha256"] = content_hash(payload)
            self.store.append(Event(self.identity, 1, "completion_prepared", payload))

    def verify(
        self, evaluator: Callable[[LogicalExperience, Execution], VerificationResult]
    ) -> VerificationResult:
        with self.store.lease(self.identity):
            if self.store.manifest(self.identity) != self.manifest:
                raise ValueError("completion provenance mismatch")
            events = self.store.events(self.identity)
            if not events or events[0].kind != "completion_prepared":
                raise ValueError("missing durable prepared completion")
            if any(e.kind == "terminal_commit" for e in events):
                raise ValueError("immutable terminal completion; duplicate verification prohibited")
            payload = events[0].payload
            if not isinstance(payload, dict):
                raise ValueError("invalid prepared completion")
            body = {k: v for k, v in payload.items() if k != "sha256"}
            if payload.get("sha256") != content_hash(body):
                raise ValueError("prepared completion integrity failure")
            safe(body)
            experience = restore(LogicalExperience, payload["experience"])
            execution = restore(Execution, payload["execution"])
            try:
                result = evaluator(experience, execution)
                if not isinstance(result, VerificationResult):
                    raise TypeError("verification result required before terminal commit")
            except Exception as exc:
                self.store.append(
                    Event(
                        self.identity,
                        len(events) + 1,
                        "completion_failure",
                        {
                            "category": type(exc).__name__,
                            "stage": "verification",
                            "resumable": True,
                            "execution_sha256": content_hash(payload["execution"]),
                        },
                    )
                )
                raise
            self.store.append(
                Event(
                    self.identity,
                    len(events) + 1,
                    "terminal_commit",
                    json_value(
                        {
                            "prepared_sha256": content_hash(payload),
                            "verification": result,
                            "execution_sha256": content_hash(payload["execution"]),
                        }
                    ),
                )
            )
            return result


class TransactionalEvaluator:
    """Wrap an existing evaluator; retained execution remains verifiable after failure.

    To recover, rebind this wrapper with the same identity/provenance and call
    verify with the durable execution. Native execution is never invoked here.
    """

    def __init__(self, evaluator: Any, transaction: CompletionTransaction) -> None:
        self.evaluator, self.transaction = evaluator, transaction

    def verify(self, experience: LogicalExperience, execution: Execution, state: Any) -> VerificationResult:
        try:
            self.transaction.store.manifest(self.transaction.identity)
        except KeyError:
            self.transaction.prepare(experience, execution)
        events = self.transaction.store.events(self.transaction.identity)
        if not events or not isinstance(events[0].payload, dict):
            raise ValueError("incomplete prepared journal; external reconciliation required")
        if content_hash(json_value(execution)) != content_hash(events[0].payload["execution"]):
            raise ValueError("prepared execution cannot be replaced")
        return self.transaction.verify(lambda exp, prepared: self.evaluator.verify(exp, prepared, state))
