# Agent ecosystem status

Reviewed 2026-10-08. Install Core with `pip install implicit-ai`. “LIVE” refers to an observed public artifact or endpoint; it does not imply directory approval, client UI verification or users.

| Surface | Status | Available path and limits |
| --- | --- | --- |
| PyPI package | LIVE | Stable 1.0.0; Python SDK, CLI and eight local MCP tools |
| Public repository plugin | LIVE source; MANUAL-CONFIGURATION-ONLY | Local skill/configuration under plugin/ and repository marketplace; Python installation remains required |
| Codex CLI, IDE, desktop local host | MANUAL-CONFIGURATION-ONLY | Documented local stdio configuration; deterministic installed-wheel MCP validation |
| ChatGPT desktop local plugin | MANUAL-CONFIGURATION-ONLY | Repository marketplace on a local host; actual desktop UI installation not asserted |
| ChatGPT web custom MCP | NOT CURRENTLY SUPPORTED by this release | Web connection requires supported HTTP/SSE transport or a compatible Secure MCP Tunnel; Core ships local stdio only |
| OpenAI public skills-only plugin | PREPARED; REQUIRES OWNER ACTION | Owner chooses verified publishing identity and submits the separate skills-only ZIP; acceptance is unverified |
| OpenAI public MCP plugin | REQUIRES OWNER ACTION | Needs approved reachable transport, ownership, policies and review; no remote service is deployed |
| Claude Code | MANUAL-CONFIGURATION-ONLY | Official stdio syntax; see MCP quickstart |
| VS Code / GitHub Copilot | MANUAL-CONFIGURATION-ONLY | Official servers configuration; see MCP quickstart |
| Cursor | MANUAL-CONFIGURATION-ONLY | Official mcpServers configuration; see MCP quickstart |
| Official MCP Registry | PREPARED | Current PyPI description lacks its ownership marker; see registry prerequisites |

[Current OpenAI MCP guidance](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) documents local client configuration. [Plugin packaging](https://developers.openai.com/plugins/build/plugins) distinguishes repository marketplaces from workspace and universal directory publication.

[Current OpenAI submission flow](https://developers.openai.com/plugins/deploy/submission) requires a verified publishing identity and portal access. Skills-only submissions do not require MCP review cases or a recording; adding MCP to an existing skills-only plugin is unsupported, so preserve separate package identities. No acceptance is implied.

[ChatGPT custom MCP guidance](https://developers.openai.com/api/docs/guides/custom-mcp-server) describes remote/tunnel connection; a local stdio executable alone is insufficient. A hosted service would require a separate scope, hosting/security design and owner decisions. Do not expose it merely to market this release.

[Claude Code](https://code.claude.com/docs/en/mcp), [VS Code](https://code.visualstudio.com/docs/agents/reference/mcp-configuration) and [Cursor](https://docs.cursor.com/context/model-context-protocol) are the configuration references. [MCP quickstart](MCP_QUICKSTART.md) contains exact snippets. Client approval and configuration remain local to the developer.
