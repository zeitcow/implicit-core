# Technical registry status

Reviewed 2026-10-15. Canonical install: `pip install implicit-ai`. Package publication, directory publication and client configuration are separate outcomes.

| Surface | State | Verified route and limits |
| --- | --- | --- |
| PyPI | LIVE | 1.0.1 metadata/documentation release. Runtime differs from 1.0.0 only in its version string; fresh canonical install and public examples passed. |
| GitHub | LIVE | Public source, release artifacts, documentation and repository plugin marketplace. |
| Official MCP Registry | LIVE | [io.github.zeitcow/implicit-core 1.0.0](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.zeitcow%2Fimplicit-core/versions/1.0.0), local stdio MCPB. |
| Glama | LIVE | [Accepted listing](https://glama.ai/mcp/servers/zeitcow/implicit-core). Local server; managed hosting is not required. Tool introspection has not completed. No quality or license letter grade is asserted. |
| Smithery | LIVE | [Implicit Core](https://smithery.ai/servers/zeitcow/implicit-core), Local, 1.0.0 MCPB and eight actual tool schemas. No hosted service or credentials required. |
| Awesome MCP Servers | AWAITING REVIEW | Existing [PR #16015](https://github.com/punkpeye/awesome-mcp-servers/pull/16015) has the accepted Glama URL and working score badge. |
| Docker MCP Registry | AWAITING REVIEW | Existing [PR #5560](https://github.com/docker/mcp-registry/pull/5560). Current contribution guidance permits third-party submissions. |
| OpenAI Plugins Directory | OWNER ACTION REQUIRED | Separate desktop skills-only package; portal authentication, verified publishing identity and review required. No directory acceptance claimed. |
| Zenodo | OWNER ACTION REQUIRED | Public stable 1.0.0 source archive and accurate software metadata prepared for owner-authenticated archival. No DOI minted. |

The official registry uses the verified [MCPB release asset](https://github.com/zeitcow/implicit-core/releases/download/v1.0.0/implicit-core-mcp-1.0.0.mcpb), SHA-256 `e1cfd860c247ebfb1553c37bebcaa5cbe56892eeb8329a289dd250363423e3f7`. It does not depend on PyPI ownership-marker verification. The older prepared PyPI manifest is an example, not the live registration.

Sources: [MCP publication](https://modelcontextprotocol.io/registry/quickstart), [Smithery publication](https://smithery.ai/docs/build/publish), [OpenAI submission](https://developers.openai.com/plugins/deploy/submission), [desktop-only rules](https://developers.openai.com/plugins/deploy/desktop-only), [Awesome rules](https://github.com/punkpeye/awesome-mcp-servers/blob/main/CONTRIBUTING.md), [Docker rules](https://github.com/docker/mcp-registry/blob/main/CONTRIBUTING.md).

No paid placement, mass submission, platform endorsement or social/community promotion is implied.
