# Plugin readiness

Public source includes portable plugin.json/mcp.json, Codex manifests, a repository marketplace and an integration skill. Install the runtime with `pip install implicit-ai`; local MCP requires Python 3.11+ and the correct executable PATH.

For a supported local Codex client:

```console
codex plugin marketplace add zeitcow/implicit-core --ref main
codex plugin add implicit-core@implicit-core
```

The skill's bundled references contain the adapter contract and integration guide. Runtime installation is separate. If a client cannot resolve `implicit-mcp`, use the absolute executable path from the [MCP quickstart](docs/MCP_QUICKSTART.md).

[Official packaging](https://developers.openai.com/plugins/build/plugins) describes repository marketplaces. The [dated ecosystem review](docs/ECOSYSTEMS.md) separates LIVE source, manual local configuration and public directory status. Manifest/schema and installed-package stdio checks do not prove desktop UI installation.

A separate skills-only ZIP is prepared for owner submission through the [current OpenAI portal](https://developers.openai.com/plugins/deploy/submission). It contains no local MCP connection. Directory acceptance remains unverified and requires owner publishing identity/access. A future MCP plugin is a separate submission: this release has no remote endpoint, hosted authentication or directory-listed server.

No listing, platform endorsement or hosted ChatGPT connection follows from repository source publication. [Registry materials](docs/REGISTRY_SUBMISSIONS.md).
