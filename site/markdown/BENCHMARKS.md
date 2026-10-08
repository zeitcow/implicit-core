# Benchmarks

In the Implicit Core v1 release-candidate benchmark, Implicit preserved equivalent state, tool behavior, and reward across 155/155 comparable cases while reducing retained serialized/materialized state by 93.88% overall and 99.55% at the median.

Implicit added approximately 0.554 seconds of mean full-pipeline latency per case in this benchmark.

## RC1 validation population

Native reference replay used the preserved 155 comparable ENV systems cases. All completed and were equivalent. This establishes systems equivalence, not agent capability or learning.

| Quantity | Measurement |
| --- | ---: |
| Eager retained serialized/materialized state | 274,839,550 bytes |
| Implicit retained serialized/materialized state | 16,808,820 bytes |
| Aggregate reduction | 93.88% |
| Mean case reduction | 94.40% |
| Median case reduction | 99.55% |
| Mean full-pipeline latency delta | +0.553819 seconds/case |
| Index storage (separate) | 5,271,552 bytes |
| Snapshot reconstruction (separate) | 258,030,730 bytes |

Retained bytes count canonical serialized runtime state. Index, journal, snapshot reconstruction and evaluator logical bytes are separate categories. No RSS or peak-memory measurement supports a RAM-saving claim. Aggregate reduction is 1 - sum(implicit)/sum(eager); mean/median use case ratios. Latency covers the pipeline including snapshot work; overhead can dominate small workloads.

The sanitized [RC1 summary](benchmarks/rc1-summary.json) supplies facts, evidence hashes and per-case numbers without task data. Implementation SHA: 82f07b35bdc78caa36888641d62835a18e5c5609. Complete evidence SHA: 34f18a8ac94cfaa0bb46dac133ec4011f4c6659e. RC1 wheel SHA-256: 111e13e1f675ee12fc56641e5c4b385d50ec9a9ce2687bb1fbe7a682877decb6.

Restricted native assets and harnesses are not shipped; the entire population cannot be independently replayed from this bundle. The summary permits arithmetic verification, not independent native replay. RC2 adds MCP; the 155-case result belongs to rc1. The audit identifies unchanged runtime modules and rc2 validation separately.

## Reproducible public workload

```console
implicit benchmark
```

The fixed toy addresses one experience with inventory, shipping policy and an unused 100,000-character payload. Eager loads all three; Implicit loads inventory and policy. Both determine and verify shipping. Output includes resource counts, canonical bytes, equivalence, seed, provenance and Implicit pipeline time. It does not measure eager latency, RAM or production scale. The coordinate-space size is not a tested capacity.

## Tested RC1 envelope

Procedural addressing was tested through 1,000,000 possible experiences, one selected record per operation. Workloads completed 20,650 lifecycle operations (1,650 durable) plus 100,000 materializations. Concurrency covers eight separate-store workers and four journal writers. Recovery covers 240 journal-boundary cases, 64 completion cases, 50/50 reconciled interruptions and 4/4 forced-death lease recoveries. Migration covers rollback/retry and incompatible-schema refusal.

Cite version/population with CITATION.cff and include approximately +0.554 seconds/case overhead whenever summarizing the reduction. No allocator, learning, RAM, SOTA, universal-superiority, unlimited-scale, global exactly-once or security-certification claim is supported.
