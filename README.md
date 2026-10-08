# Implicit

**The experience layer for AI agents.**

Virtualize large agent environments. Materialize only the state each experience actually needs.

In the Implicit Core v1 release-candidate benchmark, Implicit preserved equivalent state, tool behavior, and reward across 155/155 comparable cases while reducing retained serialized/materialized state by 93.88% overall, 94.40% mean and 99.55% at the median.

Implicit added approximately 0.554 seconds of mean full-pipeline latency per case in this benchmark.

These measurements belong to rc1, not the toy demo or new MCP interface. Serialized bytes are not RAM. [Benchmarks](BENCHMARKS.md) explains the population, methodology and limitations.

## Try the release candidate

Python 3.11+; zero third-party runtime dependencies. Build and install the public release candidate from source:

```console
python -m pip install hatchling
python -m hatchling build
python -m pip install --no-index dist/implicit_ai-1.0.0rc2-py3-none-any.whl
implicit --help
implicit --version
implicit demo
implicit benchmark
```

For the exact release artifacts, use [GitHub Releases](https://github.com/zeitcow/implicit-core/releases/tag/v1.0.0rc2). PyPI installation is `python -m pip install --pre implicit-ai` when the release is listed there; check package availability before relying on PyPI. Isolate it from the unrelated `implicit` distribution, which shares the import namespace.

## Why virtualize an experience?

An experience is one versioned, addressable environment interaction with an instruction, required state, execution and evaluation. A warehouse may contain millions of orders; processing one order needs only its inventory and policy records. Implicit retains lightweight addresses and loads pages when your adapter requests them.

Use it when environments have large unused state, repeatable identities, expensive construction, or need durable execution evidence. It can add overhead when state is small, most pages are needed, or your adapter cannot separate state. Measure your workload, including full-pipeline latency and every storage category.

## Keep your existing stack

Your adapter owns native behavior. Keep your learner, agent framework and evaluator; Core accepts ordinary Python protocols. No allocator is required. Default selection preserves your proposed order. [Create an adapter](ADAPTERS.md), or run three independent examples with the wheel installed:

```console
python -I examples/core_adapters.py
```

Core supplies versioned addresses, selective materialization, cache lifecycle, journals, recovery and provenance. It does not promise universal speedups, learning improvement, allocator superiority or arbitrary external exactly-once effects.

## Documentation

- [Quickstart](QUICKSTART.md) and [Installation](INSTALL.md)
- [Architecture](ARCHITECTURE.md), [Adapters](ADAPTERS.md) and [Configuration](CONFIGURATION.md)
- [Benchmarks](BENCHMARKS.md), [FAQ](docs/FAQ.md) and [Troubleshooting](TROUBLESHOOTING.md)
- [Security and privacy](SECURITY.md), [Local MCP](MCP.md) and [Agent integration](docs/AGENT_INTEGRATION.md)
- [Contributor commands](CONTRIBUTING.md), [Agent commands](AGENTS.md), [Citation](CITATION.cff) and [Release plan](docs/RELEASE_PLAN.md)

Demo, benchmark and local MCP make no outbound connections. Python adapters are trusted code and may use your services. See SECURITY.md for persisted fields, cleanup and trust boundaries.

Implicit Core is licensed under [Apache-2.0](LICENSE). [Licensing inventory](LICENSING_REVIEW.md) describes included assets and [NOTICE](NOTICE) preserves attribution.
