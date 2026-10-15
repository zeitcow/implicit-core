# Install the Implicit Core MCP server

Implicit is the experience layer for AI agents. The MCP interface provides eight bounded synthetic tools over local stdio. Real environment adapters use the Python SDK. No API key, service account or hosted endpoint is required.

Use Python 3.11+ in an isolated virtual environment. Install the canonical public package with `python -m pip install implicit-ai`. Check `implicit --version` and `implicit-mcp --version`. The distribution is `implicit-ai`; its import is `implicit`, which overlaps an unrelated distribution. Keep the environment isolated.

Find the installed executable with `python -c "import shutil; print(shutil.which('implicit-mcp'))"`. Configure the MCP client with this absolute path, empty arguments and stdio transport. Windows virtual environments use `Scripts/implicit-mcp.exe`; Unix environments use `bin/implicit-mcp`.

For Cline CLI, inspect `cline mcp install --help`, then use `cline mcp install --yes implicit /absolute/path/to/implicit-mcp`. If the caller supplies an isolated `--config` and `--data-dir`, pass those global options to every Cline command. Preserve the caller's existing servers. For the Cline extension, add the stdio server through its MCP settings. Restart or reload the client after configuration so it discovers tools.

Expected tools: `implicit_create_universe`, `implicit_inspect_universe`, `implicit_address_experience`, `implicit_materialize`, `implicit_inspect_state`, `implicit_get_provenance`, `implicit_benchmark`, `implicit_validate_adapter`.

Verify using actual MCP calls: create a universe with `count: 1000`, inspect its returned `universe_id`, run `implicit_benchmark` with `{}`, and run `implicit_validate_adapter` with `{}`. Check successful responses, benchmark `semantic_equivalence: true` and adapter `passed: true`. These checks cover a fixed synthetic interface, not custom user-code execution or reproduction of the release-candidate benchmark.

The server waits on stdin and reserves stdout for JSON-RPC. Running it without a client does not open a web service. State is bounded process memory and disappears on restart. Use the [MCP quickstart](docs/MCP_QUICKSTART.md) for other clients and [MCP documentation](MCP.md) for bounds and schemas.
