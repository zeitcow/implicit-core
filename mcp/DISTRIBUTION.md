# Distribution packaging

Canonical install remains `pip install implicit-ai`; launch `implicit-mcp` over local stdio.

The root Dockerfile installs the exact released 1.0.0 wheel with its PyPI SHA256 and starts the server as an unprivileged user. Build needs PyPI access; runtime needs no network, credentials or services. The MCP distribution workflow verifies initialization and eight-tool introspection with container networking disabled. Supply this Dockerfile directly through Glama after claiming the listing; a repository file alone does not complete Glama validation.

`mcp/server.json` describes an optional MCPB artifact built from unchanged package files in the released PyPI wheel. The bundle requires Python 3.11+ available as `python`; it is a packaging option, not a new hosted server. Its file hash is checked by clients. `server.prepared.json` preserves the separate PyPI publication template; that route still requires the ownership marker in a future justified package release.

The server remains bounded to synthetic in-memory experience addressing, materialization, provenance, benchmarking and adapter rehearsal. Real environments use SDK adapters. Directory publication, review and acceptance are separate external operations and cannot be inferred from these files.
