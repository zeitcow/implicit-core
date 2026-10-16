# Architecture

## A large environment, a small episode

Implicit Core represents agent experience/environment state as versioned addresses and loadable resources. In a training or evaluation system, the set of possible orders, tasks or scenarios may be much larger than the state one episode requires. The adapter can describe that space without building every scenario, then materialize the selected experience's required pages on demand.

## Address, plan, load, execute

An immutable Universe identifies experiences by identity/version/coordinate. propose supplies a bounded sequence; probe supplies lightweight metadata without full state. Core follows external proposal order and needs no adaptive allocator.

Environment builds a MaterializationPlan and versioned ResourceSource. PagedState loads initial resources, then resolves reads and dependencies in the same Python call stack. Cycles and absent records fail. Source versions isolate cache entries; coordinate identity prevents cross-experience contamination. Episode-local writes do not change pristine cache contents.

The adapter must keep proposal, probe and planning lightweight and defer state construction to ResourceSource. Initial pages and declared dependencies are part of the required state; an experience that needs every page will still load every page. Cross-page invariants remain the adapter's responsibility.

Your adapter owns execution. Your agent/framework stays bound as an ordinary Python object; your evaluator owns reward and verification. Optional ExternalLearner updates are application-owned; Core makes no learning improvement claim.

## Reproducibility conditions

An experience address identifies the universe identity, version and coordinate. Versioned sources and recorded resource hashes support checking which state was used; seeded execution streams support repeatable runs. Reproduction also requires the same contents behind immutable versions, fixed root seeds, compatible pinned agents/adapters and deterministic state generation and execution. Live services, nondeterministic agents and external effects require application-owned capture, control or reconciliation. A version label or provenance hash alone cannot make an arbitrary external program deterministic.

## The environment-state layer

The address and pages describe logical agent state, rather than a machine image. VM snapshotting, VM forks and container copy-on-write clone execution environments; they can host an Implicit adapter. Filesystem paging and dataset streaming move bytes or records; the adapter decides how those records form an experience and its dependencies. Prompt/context compression changes model input. Lazy MCP tool discovery changes when tool definitions are exposed. These mechanisms can complement experience addressing, but do not supply its environment-state contract by themselves.

## Evidence, recovery and bounds


MemoryStore or SQLiteEventStore records lifecycle events. Optional content storage retains canonical bytes. Checksums support corruption detection and recovery; they do not authenticate hostile modifications. Compatible agents/environments must be explicitly rebound. Incomplete episodes refuse automatic replay: reconcile external effects before explicitly abandoning an interrupted episode.

Cache capacity bounds retained pages, not active dependency closures, arrays, working state or RAM. Sessions are thread-affine. Independent worker transports/stores are the documented pattern. Journals grow until caller-managed cleanup.

Local MCP wraps bounded synthetic addressing and Core paging. It accepts no Python imports, paths or shell commands, and exposes no user agent execution. Use the SDK for real adapters.
