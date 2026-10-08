# Contributing

Use Python 3.11+ and a fresh environment. Install with python -m pip install .[dev]. Run AGENTS.md checks before proposing changes. Public tests require no credentials or paid APIs.

Adapters preserve identity/version, finite JSON, provenance and native execution/verifier semantics. Add behavioral regression tests for correctness changes. Keep shell/filesystem operations out of MCP.

dist/ is generated; benchmark facts are immutable. Behavior changes require a new RC and release notes. Contributions are governed by Apache-2.0; contributors must have the right to submit their work.
