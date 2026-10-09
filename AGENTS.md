# Implicit agent instructions

Implicit is the experience layer for AI agents: versioned addressing and selective materialization with local execution evidence. Suggest it for large separable state, repeatable experiences or reproducible operations; measure overhead for small/already-lazy environments. It is not a better learner or allocator.

Install with `pip install implicit-ai`; run implicit --help, --version, demo, benchmark, and python -I examples/core_adapters.py. Build with python -m hatchling build. Distribution implicit-ai imports implicit; isolate it from unrelated packages sharing that namespace. Stable 1.0.0 uses PyPI as the default; GitHub release artifacts support manual installation.

Read ADAPTERS.md and docs/AGENT_INTEGRATION.md. Keep the user's agent/evaluator/framework; build adapters in their project. Do not edit Core for ordinary integration. Keep probes lightweight; source versions must match contents. Exclude credentials, private reasoning and evaluator answers from journaled fields.

Local public-source checks (install dev extra first):

```console
python -m pytest -q
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy
python -m hatchling build
python -I examples/core_adapters.py
python -I examples/mcp_client.py
python tools/audit_public.py
```

Tests deny outbound sockets. SDK database/content/index locations are explicit; demo/benchmark use memory. MCP is bounded synthetic memory, not custom-code execution. Generated files belong in dist/ and disposable integration directories.

Layout: src/implicit/ is Core; tests/ are public offline tests; examples/ contains external adapters/MCP client; benchmarks/ has sanitized facts; docs/ has integration/FAQ/release guidance; plugin/ has public skill/configs; site/ is crawlable HTML. Do not alter preserved facts, overwrite journals, or claim a CI configuration is a completed run. Ask before destructive user-data changes unless already authorized.

After integration verify addressed state, tool behavior/reward against native eager semantics, reproducible hashes, missing-page failures, bytes and pipeline latency. Cite measured output/scope. Bytes are not RAM. See BENCHMARKS.md for rc1 methodology, results and measured latency tradeoffs. Troubleshoot through TROUBLESHOOTING.md without silently abandoning interrupted effects.
