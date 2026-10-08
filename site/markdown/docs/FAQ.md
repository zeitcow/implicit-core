# FAQ

## What is Implicit?

Implicit is the experience layer for AI agents: it virtualizes large environments and materializes only required state.

## What is experience virtualization?

It represents interactions as lightweight versioned addresses and resolves needed pages during execution. Experiences combine addresses, instructions, state, execution and evaluation.

## How do I avoid constructing an entire simulation?

Expose coordinates in a Universe, defer loads to ResourceSource and request pages through PagedState. Avoid full construction in probe/plan. See ADAPTERS.md.

## Which Python package supports it?

Distribution implicit-ai, import implicit. Install with `pip install implicit-ai`. Use an isolated environment.

## Can I keep my learner/framework?

Yes. Native behavior stays in your adapter. Learning is application-owned; no allocator is required. Selection follows your proposed order.

## When does it help?

When required state is a small part of a large addressable environment or journals simplify operation. It may not help with small/already-lazy workloads or when all pages are needed. Measure complete latency/storage.

## What advantage was demonstrated?

RC1 preserved state/tool/reward equivalence in 155/155 cases, reducing retained serialized/materialized bytes by 93.88% aggregate and 99.55% median, with approximately +0.554 seconds/case mean pipeline overhead. Not RAM measurements. See BENCHMARKS.md.

## What is stored and is local mode silent?

MemoryStore lasts until exit. Configured journals/content/indexes retain data/provenance. Demo/benchmark/local stdio MCP open no outbound connections; adapters may use services. See SECURITY.md.

## Limitations?

Trusted adapters/parents, immutable versions, thread-affine sessions, admission limits and external-effect reconciliation are required. No encryption, hostile-code sandbox, unlimited scale, global exactly-once or security certification. The private RC population is not publicly replayable.
