# Architecture

An immutable Universe identifies experiences by identity/version/coordinate. propose supplies a bounded sequence; probe supplies lightweight metadata without full state. Core follows external proposal order and needs no adaptive allocator.

Environment builds a MaterializationPlan and versioned ResourceSource. PagedState loads initial resources, then resolves reads and dependencies in the same Python call stack. Cycles and absent records fail. Source versions isolate cache entries; coordinate identity prevents cross-experience contamination. Episode-local writes do not change pristine cache contents.

Your adapter owns execution. Your agent/framework stays bound as an ordinary Python object; your evaluator owns reward and verification. Optional ExternalLearner updates are application-owned; Core makes no learning improvement claim.

MemoryStore or SQLiteEventStore records lifecycle events. Optional content storage retains canonical bytes. Checksums support corruption detection and recovery; they do not authenticate hostile modifications. Compatible agents/environments must be explicitly rebound. Incomplete episodes refuse automatic replay: reconcile external effects before explicitly abandoning an interrupted episode.

Cache capacity bounds retained pages, not active dependency closures, arrays, working state or RAM. Sessions are thread-affine. Independent worker transports/stores are the documented pattern. Journals grow until caller-managed cleanup.

Local MCP wraps bounded synthetic addressing and Core paging. It accepts no Python imports, paths or shell commands, and exposes no user agent execution. Use the SDK for real adapters.
