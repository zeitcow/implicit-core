"""No implied free work: stage durations, failed operations and unknown prices are explicit."""

import math
from collections import defaultdict
from contextlib import contextmanager
from time import perf_counter
from typing import Callable, Iterator, TypeVar

T = TypeVar("T")


class Accounting:
    def __init__(self) -> None:
        self.values: dict[str, int | float] = defaultdict(int)

    def add(self, name: str, amount: int | float = 1) -> None:
        if not math.isfinite(amount) or amount < 0:
            raise ValueError(f"{name}: measurement must be finite and nonnegative")
        self.values[name] += amount

    def cost(self, stage: str, usd: float | None) -> None:
        if usd is not None and (not math.isfinite(usd) or usd < 0):
            raise ValueError("price must be finite and nonnegative")
        self.add(f"{stage}_cost_unknown" if usd is None else f"{stage}_cost_reports")
        if usd is not None:
            self.add(f"{stage}_cost_usd", usd)
            self.add("reported_cost_usd", usd)

    def reconcile(self, stage: str, total_usd: float, already_reported: float) -> None:
        if any(not math.isfinite(x) or x < 0 for x in (total_usd, already_reported)):
            raise ValueError("reconciled prices must be finite and nonnegative")
        if total_usd < already_reported:
            raise ValueError("reconciliation cannot erase previously reported usage")
        self.cost(stage + "_reconciled", total_usd - already_reported)

    def reward(self, value: float) -> None:
        # RL rewards may be negative; measurement counters and prices may not.
        if not math.isfinite(value):
            raise ValueError("reward must be finite")
        self.values["reward_sum"] += value

    def invoke(self, stage: str, call: Callable[[], T], price: Callable[[T], float | None]) -> T:
        try:
            with self.time(stage):
                result = call()
                self.cost(stage, price(result))
        except Exception:
            self.cost(stage, None)
            raise
        return result

    @contextmanager
    def time(self, stage: str) -> Iterator[None]:
        start = perf_counter()
        try:
            yield
        except Exception:
            self.add(f"{stage}_errors")
            raise
        finally:
            self.add(f"{stage}_seconds", perf_counter() - start)

    def snapshot(self) -> dict[str, int | float]:
        return dict(sorted(self.values.items()))
