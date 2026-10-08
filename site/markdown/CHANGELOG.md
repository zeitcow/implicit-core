# Changelog

## 1.0.0 — stable release

Promotes the validated 1.0.0rc2 public source to stable 1.0.0 with version metadata, release documentation and Trusted Publishing workflow updates. Canonical installation: `pip install implicit-ai`. Adds the required package `implicit.__version__` metadata; execution, storage and materialization behavior are unchanged. Stable artifacts differ from RC2 and have their own checksums. The v1.0.0rc2 tag and assets remain historical evidence.

The preserved rc1 benchmark remains 155/155 equivalent cases, 93.88% aggregate, 94.40% mean and 99.55% median retained serialized/materialized-state reduction, with approximately +0.554 seconds/case mean full-pipeline latency overhead. Bytes are not RAM; this promotion does not create a new native benchmark result.

## 1.0.0rc2 — initial public preview

Adds bounded local stdio MCP, client/schema tests, deterministic public extraction, agent/plugin assets, crawlable documentation and launch rehearsals. Public metadata excludes research dependencies; CLI doctor reports Core rather than private adapter availability. Core execution/storage/materialization remain inherited from rc1; no new native 155-case result is claimed.

## 1.0.0rc1 — internal

Preserved systems equivalence in the 155-case population, durable recovery/migration, bounded residency and external adapter integration. Retained serialized/materialized bytes fell 93.88% overall and 99.55% median with approximately +0.554 seconds/case mean pipeline overhead. Not RAM or learning claims.
