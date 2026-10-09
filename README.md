# Implicit

**The experience layer for AI agents.**

Virtualize large agent environments. Materialize only the state each experience actually needs.

```console
pip install implicit-ai
```

[Website and docs](https://zeitcow.github.io/implicit-core/) · [PyPI](https://pypi.org/project/implicit-ai/) · [60-second quickstart](QUICKSTART.md) · [Measured evidence](BENCHMARKS.md) · [Connect a coding agent](docs/MCP_QUICKSTART.md) · [Install the Codex integration skill](https://github.com/zeitcow/implicit-core/tree/main/plugins/implicit-integration)

## Why virtualize an experience?

Large agent environments often contain far more possible state than one interaction needs. A warehouse may contain millions of orders; processing one order needs only its inventory and policy records. Implicit keeps versioned addresses and loads pages when your adapter requests them.

An experience is one addressable interaction: instruction, required state, execution and evaluation. The address identifies the environment version and coordinate. Your adapter chooses pages; your existing agent executes; your native evaluator verifies the result. Core records execution state, provenance and explicit recovery.

Use Implicit for large separable state, repeatable identities, expensive environment construction or durable execution evidence. Measure overhead for small, already lazy or mostly accessed environments.

## Try it in 60 seconds

Python 3.11+; zero third-party runtime dependencies. In a fresh virtual environment:

```console
pip install implicit-ai
implicit --version
implicit demo
implicit benchmark
```

The public toy compares eager and selective serialized state, verifies the shipping result and prints a provenance hash. Its output is its own workload measurement.

The distribution is `implicit-ai`; the import is `implicit`. Use an isolated environment because the unrelated `implicit` recommendation library shares that import namespace. [Installation](INSTALL.md) includes Windows setup and verified [release artifacts](https://github.com/zeitcow/implicit-core/releases/tag/v1.0.0).

## Measured evidence and its limits

In the preserved **rc1** native systems population, 155/155 comparable cases preserved equivalent state, tool behavior and reward.

| Measurement | Result |
| --- | ---: |
| Aggregate retained serialized/materialized-state reduction | 93.88% |
| Mean case reduction | 94.40% |
| Median case reduction | 99.55% |

Serialized/materialized bytes are **not RAM**. The measurements belong to rc1, not a new 1.0.0 native replay or the toy/MCP demo. The public numeric summary supports arithmetic verification; restricted native replay assets are not shipped. [Methodology, measured latency tradeoffs, hashes and limitations](BENCHMARKS.md).

## Keep your existing stack

Keep your agent, learner, framework and evaluator. Build an adapter in your project using ordinary Python protocols:

```text
Universe proposes versioned addresses
  -> Environment plans required pages
  -> ResourceSource loads pages as needed
  -> existing agent executes
  -> native Evaluator verifies
  -> Core records provenance and recovery state
```

[Adapter contract](ADAPTERS.md), [agent integration prompts](docs/AGENT_INTEGRATION.md) and [three public adapter shapes](examples/core_adapters.py) show the mapping. With the public repository downloaded and the package installed:

```console
python -I examples/core_adapters.py
```

No allocator or new learner is required. Default selection preserves your proposed order. Core does not establish improved learning, general speedups, allocator superiority or universal infrastructure guarantees.

## Let a coding agent try Implicit

The package includes eight bounded local stdio MCP tools for synthetic addressing, paging, provenance and validation. [MCP quickstart](docs/MCP_QUICKSTART.md) gives Codex, Claude Code, VS Code and Cursor configurations. Real environment adapters use the Python SDK.

[Repository plugin](PLUGIN_READINESS.md) packages integration guidance and local MCP configuration. Public directory acceptance and hosted ChatGPT connectivity are separate; see the dated [ecosystem status](docs/ECOSYSTEMS.md).

## Documentation

- [Quickstart](QUICKSTART.md), [installation](INSTALL.md) and [architecture](ARCHITECTURE.md)
- [Adapters](ADAPTERS.md), [configuration](CONFIGURATION.md) and [agent integration](docs/AGENT_INTEGRATION.md)
- [Benchmarks](BENCHMARKS.md), [citation guide](docs/CITING.md) and [FAQ](docs/FAQ.md)
- [Local MCP](MCP.md), [MCP quickstart](docs/MCP_QUICKSTART.md) and [ecosystem status](docs/ECOSYSTEMS.md)
- [Security and privacy](SECURITY.md), [troubleshooting](TROUBLESHOOTING.md) and [contributing](CONTRIBUTING.md)
- [Agent commands](AGENTS.md), [release history](CHANGELOG.md) and [public adoption measurement](docs/ADOPTION.md)

Demo, benchmark and local MCP make no outbound connections. Python adapters are trusted application code and may use your services. There is no product telemetry. Journals may retain application data; see [SECURITY.md](SECURITY.md).

Implicit Core 1.0.0 is licensed under [Apache-2.0](LICENSE). [Licensing inventory](LICENSING_REVIEW.md) and [NOTICE](NOTICE) describe included assets.
