# Agent ecosystem status

Reviewed 2026-10-15. Install Core with `pip install implicit-ai`. LIVE identifies an observed artifact or listing; it does not imply client UI verification or adoption.

| Surface | State | Available path and limits |
| --- | --- | --- |
| PyPI | LIVE | 1.0.1 metadata/documentation update preserves 1.0.0 runtime behavior. SDK, CLI and eight local MCP tools. |
| Codex repository marketplace | LIVE | Public Git marketplace installation and enabled integration skill verified in a fresh profile. Python installation remains separate. |
| OpenAI desktop integration skill | OWNER ACTION REQUIRED | Separate skills-only package requires local execution. Portal authentication, verified identity and review remain necessary. |
| OpenAI local MCP plugin | OWNER ACTION REQUIRED | [Desktop-only rules](https://developers.openai.com/plugins/deploy/desktop-only) require approved-partner organization allowlisting. |
| ChatGPT web custom MCP | NOT APPLICABLE | This release supplies local stdio, with no public HTTP endpoint. |
| Glama | LIVE | [Accepted local listing](https://glama.ai/mcp/servers/zeitcow/implicit-core); platform introspection not complete. |
| Smithery | LIVE | [Local MCPB listing](https://smithery.ai/servers/zeitcow/implicit-core), version 1.0.0 and eight tools. |
| Official MCP Registry | LIVE | `io.github.zeitcow/implicit-core`, version 1.0.0, local stdio MCPB. |
| Awesome MCP Servers | AWAITING REVIEW | [PR #16015](https://github.com/punkpeye/awesome-mcp-servers/pull/16015). |
| Docker MCP Registry | AWAITING REVIEW | [PR #5560](https://github.com/docker/mcp-registry/pull/5560). |

Install the integration skill:

```console
codex plugin marketplace add zeitcow/implicit-core --ref main
codex plugin add implicit-integration@implicit-core
```

This skill contains adapter guidance and references. The separate `implicit-core@implicit-core` package includes local MCP configuration. [Plugin readiness](../PLUGIN_READINESS.md) explains the scopes.

[Claude Code](https://code.claude.com/docs/en/mcp), [VS Code / Copilot](https://code.visualstudio.com/docs/agents/reference/mcp-configuration), [Cursor](https://cursor.com/docs/mcp) and Cline support local stdio configuration. [MCP quickstart](MCP_QUICKSTART.md) provides setup and bounded tool scope. Configuration support does not establish curated marketplace acceptance.

[OpenAI packaging](https://developers.openai.com/plugins/build/plugins) and [submission](https://developers.openai.com/plugins/deploy/submission) distinguish repository distribution from the reviewed directory. Desktop-only skills declare `requires_local_executor`; local MCP submissions additionally require partner allowlisting. No directory acceptance is implied.
