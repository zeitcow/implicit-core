# Local MCP

Install with `pip install implicit-ai` in a fresh environment; see INSTALL.md. implicit-mcp --version and --help work independently; implicit-mcp serves newline-delimited UTF-8 JSON-RPC on stdio. No cloud or authentication is required.

See the [MCP quickstart](docs/MCP_QUICKSTART.md) for absolute executable paths, current client-specific commands and first tool workflow.

## Client configuration

Codex config snippet (merge into your config, with executable on PATH):

```toml
[mcp_servers.implicit]
command = "implicit-mcp"
```

Generic local MCP:

```json
{"mcpServers":{"implicit":{"command":"implicit-mcp","args":[]}}}
```

The plugin supplies portable/Codex configurations. They require an installed wheel and correct PATH and do not install Python.

## Tools and effects

| Tool | Input | Effect |
| --- | --- | --- |
| implicit_create_universe | count: 1..1,000,000 | Creates synthetic universe in memory |
| implicit_inspect_universe | universe_id | Reads known metadata |
| implicit_address_experience | universe_id, coordinate | Creates address without pages |
| implicit_materialize | universe_id, coordinate, resource: inventory or policy | Loads fixed resource via Core paging |
| implicit_inspect_state | universe_id, coordinate | Reads materialization metadata |
| implicit_get_provenance | universe_id, coordinate | Reads address, source version and hashes |
| implicit_benchmark | empty object | Runs fixed public toy in ephemeral memory |
| implicit_validate_adapter | empty object | Validates built-in warehouse contract only |

Initialize, send notifications/initialized, then tools/list. Create a universe of count 1000, use the returned handle, address coordinate 7, materialize inventory/policy, inspect state/provenance, and benchmark. Unknown arguments/handles/resources, booleans as integers and out-of-range coordinates fail. Tool failures use isError; protocol failures use JSON-RPC errors. Listed protocols run from 2024-11-05 to 2025-11-25.

Max 16 universes/64 addresses per process; max 65,536 bytes/message. Oversized frames close the process. Read-only tools do not load missing pages. Hashes are fingerprints, not signatures. Handles reference the same trusted warehouse model, not arbitrary data isolation boundaries.

No sockets, shell, arbitrary paths, dynamic user imports or user agent execution. State is synthetic/process-local; restart discards it. Clients may log output. Real adapters and durable execution use the SDK; MCP validation does not certify custom adapters. See SECURITY.md.

Generic stdio is tested from the wheel. No marketplace install or hosted ChatGPT connection is claimed. Directory submission requires the current platform review process; no remote endpoint is deployed here. See PLUGIN_READINESS.md and the [MCP transport specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports).
