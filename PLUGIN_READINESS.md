# Plugin readiness

Public source includes portable plugin.json/mcp.json, Codex manifests, a repository marketplace and an integration skill. Install the runtime with `pip install implicit-ai`; local MCP requires Python 3.11+ and the correct executable PATH.

For a supported local Codex client:

```console
codex plugin marketplace add zeitcow/implicit-core --ref main
codex plugin add implicit-core@implicit-core
```

The skill's bundled references contain the adapter contract and integration guide. Runtime installation is separate. If a client cannot resolve `implicit-mcp`, use the absolute executable path from the [MCP quickstart](docs/MCP_QUICKSTART.md).

[Official packaging](https://developers.openai.com/plugins/build/plugins) describes repository marketplaces. The [dated ecosystem review](docs/ECOSYSTEMS.md) separates LIVE source, manual local configuration and public directory status. Manifest/schema and installed-package stdio checks do not prove desktop UI installation.

A separate desktop-only skills ZIP is published as a release asset. On 2026-10-15, a verified owner account uploaded the integration package to the [OpenAI portal](https://developers.openai.com/plugins/deploy/submission), creating a draft. It contains no MCP connection and declares `requires_local_executor` under `extensions.com.openai`, because its SDK workflows need local execution. The portal reports that it is not accepting more skills-only submissions, and also flags missing privacy-policy and terms URLs. The draft is not submitted for review or published; supplying legal URLs would not remove the independent intake restriction. Repository marketplace distribution remains available. A local MCP plugin is a separate submission and currently requires approved-partner organization allowlisting under the official desktop-only submission guide. This release has no remote endpoint or hosted authentication.

No listing, platform endorsement or hosted ChatGPT connection follows from repository source publication. [Registry materials](docs/REGISTRY_SUBMISSIONS.md).
