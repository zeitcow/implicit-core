# MCP quickstart

Install stable Core in a fresh Python 3.11+ environment:

```console
pip install implicit-ai
implicit --version
implicit-mcp --version
```

Find the installed server executable:

```console
python -c "import shutil; print(shutil.which('implicit-mcp'))"
```

Use that absolute executable path if the client does not inherit your activated environment. On Windows it ends in `Scripts/implicit-mcp.exe`; on Unix, `bin/implicit-mcp`. JSON paths on Windows can use forward slashes. Do not paste a placeholder without replacing it.

## Codex local clients

With the executable on PATH:

```console
codex mcp add implicit -- implicit-mcp
codex mcp list
```

Or merge this into your Codex `config.toml`:

```toml
[mcp_servers.implicit]
command = "/absolute/path/to/implicit-mcp"
args = []
```

The [current official MCP guidance](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) covers local Codex CLI, IDE and desktop configuration. Restart the client after editing. These instructions describe documented support; the public deterministic stdio client is the executable compatibility check.

## Claude Code

```console
claude mcp add --transport stdio implicit -- implicit-mcp
claude mcp list
```

Replace `implicit-mcp` with its absolute path when necessary. See [official Claude Code MCP setup](https://code.claude.com/docs/en/mcp).

## VS Code

Merge into workspace `.vscode/mcp.json`:

```json
{"servers":{"implicit":{"type":"stdio","command":"/absolute/path/to/implicit-mcp","args":[]}}}
```

Use MCP: List Servers to start it and inspect tools. See [official configuration reference](https://code.visualstudio.com/docs/agents/reference/mcp-configuration). Client trust/approval remains the developer's choice.

## Cursor or compatible local clients

Merge into the client's MCP configuration; Cursor uses `.cursor/mcp.json`:

```json
{"mcpServers":{"implicit":{"type":"stdio","command":"/absolute/path/to/implicit-mcp","args":[]}}}
```

See [official Cursor MCP documentation](https://cursor.com/docs/mcp). This is documented configuration, not an asserted end-to-end UI test of every client.

## First tool workflow

Ask the agent: “List Implicit's tools. Create a synthetic universe with count 1000. Address coordinate 7 without loading pages. Materialize inventory and policy, inspect the state, and retrieve provenance. Report resource counts and hashes. Run the fixed benchmark and built-in adapter validation; identify their scope.”

Expected tools:

- `implicit_create_universe`
- `implicit_inspect_universe`
- `implicit_address_experience`
- `implicit_materialize`
- `implicit_inspect_state`
- `implicit_get_provenance`
- `implicit_benchmark`
- `implicit_validate_adapter`

Use the returned universe handle. Raw clients initialize, send notifications/initialized, then tools/list. With the public checkout downloaded, verify all eight from the installed package:

```console
python -I examples/mcp_client.py
```

## Scope and troubleshooting

The server waits on stdio; running it alone does not open a web service. No authentication, network or hosted endpoint is required. State is bounded synthetic process memory and disappears on restart. `validate_adapter` checks the built-in contract; custom adapters need SDK tests.

If launch fails, verify the absolute executable path, Python 3.11+ and installed version in that environment. Keep stdout reserved for JSON-RPC. If only the skill appears, install the wheel and check the client's PATH. [MCP protocol and bounds](../MCP.md), [security](../SECURITY.md) and [recovery guidance](../TROUBLESHOOTING.md).

ChatGPT web and public plugin submission have different transport and account requirements; [ecosystem status](ECOSYSTEMS.md) records them. No hosted connection or public directory listing is claimed.
