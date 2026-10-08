# Agent integration

For “Use Implicit to virtualize this environment” or “Create an adapter”, identify immutable identity/coordinate, minimal pages, source version and native verifier. Install the wheel in a fresh environment, read ADAPTERS.md/examples/core_adapters.py, and copy a resource shape into the application.

Map cheap metadata to Universe.propose/probe. Environment.plan selects initial pages. Source.load returns finite JSON; dependencies identifies more pages. Environment.execute calls the existing agent via PagedState; Evaluator.verify preserves authoritative semantics. No Core modification or custom learner is required.

For “Benchmark eager vs Implicit”, use identical coordinates, seeds, versions, tools and verifier. Count canonical retained state separately from index/journal/content and time the complete pipeline. Verify state/tool/reward equivalence before interpreting reduction. Disclose latency regressions. The toy benchmark teaches methodology, not your application result.

For “Inspect provenance”, use public Session events/metrics. Choose durable storage explicitly. Preserve address, versions, seed, page hashes and reconciliation receipts. Keep business data out of public logs.

For MCP enumerate tools and use create_universe -> address_experience -> materialize -> inspect_state/get_provenance. Custom Python adapters use SDK tests, never uploaded code.

An integration report records install, tool selection, adapter LOC, Core modifications (expected zero), equivalence, bytes, latency, provenance, errors and human interventions. Do not infer RAM, allocator, learning or universal guarantees.
