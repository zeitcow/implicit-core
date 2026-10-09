# Agent integration

Implicit is the experience layer for AI agents. Use it when an environment has large separable state, repeatable versioned experiences or reproducible operations. Measure overhead for small, already lazy or mostly accessed state.

## Install Implicit

Prompt: “Install Implicit in a fresh environment with `pip install implicit-ai`. Verify version 1.0.0, import `implicit`, and run `implicit --help`, `implicit demo` and `implicit benchmark`. Report the package/version and toy scope. Avoid the unrelated `implicit` distribution.”

## Integrate this environment

Prompt: “Read the [adapter contract](https://zeitcow.github.io/implicit-core/adapters.html) and [three external adapter shapes](https://github.com/zeitcow/implicit-core/blob/main/examples/core_adapters.py). Map this environment's immutable identity, coordinate, minimal pages, source version and native verifier. Keep our agent, framework, learner and evaluator. Implement the adapter in our project with zero Core edits. Measure before recommending adoption.”

Universe.propose/probe expose cheap address metadata. Environment.plan chooses initial pages. ResourceSource.load returns finite JSON and dependencies names additional pages. Environment.execute calls the existing agent through PagedState. Evaluator.verify preserves the authoritative state/tool/reward semantics.

## Create an Implicit adapter

Prompt: “Create Universe, Environment, ResourceSource and Evaluator implementations for this application. Tie source versions to contents, keep probes lightweight, raise KeyError for missing pages, and use explicit SDK storage paths. Verify addresses and versions, state/tool/reward equivalence, deterministic hashes and missing-page failures. Exclude credentials, evaluator answers and private reasoning from journaled fields.”

Reuse a shape from `examples/core_adapters.py`. Import PagedState from `implicit.materialization`; MissingStateError subclasses KeyError. Ordinary integration changes no Core runtime.

## Benchmark eager versus Implicit

Prompt: “Compare native eager and Implicit execution using identical coordinates, seeds, tools, data versions and verifier. Confirm equivalence first. Record retained canonical serialized/materialized bytes separately from index, journal, content and reconstruction storage. Time the complete pipeline on both paths. Report sample count, per-case/aggregate bytes, pipeline latency delta, reproducible hashes, missing-page failures and all limitations.”

Report full-pipeline overhead, including regressions. Bytes are not RAM. The public toy teaches methodology and does not reproduce the restricted rc1 population. Historical rc1 summaries carry approximately +0.554 seconds/case mean pipeline overhead.

## Use the local Implicit MCP

Prompt: “Follow the [MCP quickstart](https://zeitcow.github.io/implicit-core/mcp_quickstart.html). Enumerate tools, create a synthetic universe, address one experience, materialize inventory/policy, inspect state/provenance, and run the fixed benchmark. Explain the built-in validation scope. Use SDK tests for custom adapters.”

MCP does not accept custom Python execution or application datasets. Use the SDK for real adapters and durable execution.

## Preserve execution evidence

Choose durable storage explicitly. Record addresses, versions, seeds, page hashes and reconciliation receipts; preserve user journals. Reconcile interrupted external effects before explicit abandonment or replay. [Troubleshooting](https://zeitcow.github.io/implicit-core/troubleshooting.html) explains recovery.

An integration report records installation, adapter LOC, Core modification count (expected zero), addressed state, native equivalence, bytes, latency, provenance, errors and human interventions. Do not infer learning, allocator, RAM or universal guarantees. Share only sanitized public evidence.
