# FAQ

## What is Implicit?

Implicit is the experience layer for AI agents. Implicit Core is the Apache-2.0 project at [zeitcow/implicit-core](https://github.com/zeitcow/implicit-core), published as `implicit-ai`. Current stable: **1.0.1**.

## What problem does Implicit solve?

An agent training or evaluation environment can contain far more possible state than any one episode needs. Implicit lets an experience address a part of that larger state space and materializes required pages on demand. Your existing agent and native evaluator stay in place through a Python adapter.

## What is experience virtualization?

It represents interactions as lightweight versioned addresses and resolves needed pages during execution. Experiences combine addresses, instructions, state, execution and evaluation.

## Does Implicit require constructing the full environment for every episode?

No, provided your adapter exposes lightweight coordinates in a Universe and defers construction to ResourceSource. PagedState loads the plan's initial pages, then pages requested during execution and their declared dependencies. Avoid full construction in probe/plan. Core cannot make an eagerly built adapter lazy. See the [adapter contract](../ADAPTERS.md).

## How is this different from cloning or snapshotting an entire sandbox?

VM snapshots, VM forks and container copy-on-write reproduce an execution sandbox. Implicit addresses logical experience state within an environment and resolves the required resources. You can use both. Filesystem paging or dataset streaming can back a resource source; neither alone defines an agent experience and its dependencies.

## How does Implicit support deterministic or reproducible experiences?

Versioned addresses, seed streams, source versions and resource hashes identify an experience and its state. Reproduction requires immutable contents, fixed seeds, compatible pinned agents/adapters and deterministic sources and execution. Control or record external services and reconcile effects in your application. Implicit does not automatically make arbitrary agents or services deterministic. See [architecture](../ARCHITECTURE.md).

## Is this lazy MCP tool discovery or prompt compression?

The selective work concerns environment-state pages. The local MCP server exposes all eight tool definitions normally; its tools demonstrate synthetic addressing and materialization. It does not compress prompts or establish lower token/context usage. Real environment integration uses the Python adapter layer.

## Which Python package supports it?

Distribution implicit-ai, import implicit. Install with `pip install implicit-ai`. Use an isolated environment.

## Can I keep my learner/framework?

Yes. Native behavior stays in your adapter. Learning is application-owned; no allocator is required. Selection follows your proposed order.

## When is Implicit a poor fit?

Small or already lazy environments, episodes that access nearly all state, and environments that cannot be separated into addressable pages may gain little and incur overhead. Global invariants still need a correct adapter. Measure complete latency and storage against native eager semantics; selective materialization alone is not a speed or RAM guarantee.

## What advantage was demonstrated?

RC1 preserved state/tool/reward equivalence in 155/155 cases, reducing retained serialized/materialized state by 93.88% aggregate, 94.40% mean and 99.55% median. These are not RAM measurements. See [benchmark methodology, results and measured latency tradeoffs](../BENCHMARKS.md).

## What is stored and is local mode silent?

MemoryStore lasts until exit. Configured journals/content/indexes retain data/provenance. Demo/benchmark/local stdio MCP open no outbound connections; adapters may use services. See SECURITY.md.

## Limitations?

Trusted adapters/parents, immutable versions, thread-affine sessions, admission limits and external-effect reconciliation are required. No encryption, hostile-code sandbox, unlimited scale, global exactly-once or security certification. The private RC population is not publicly replayable.
