# Plugin readiness

Public source includes portable plugin.json and mcp.json, Codex compatibility manifests, a reusable integration skill and a repository marketplace catalog. Install with `pip install implicit-ai`. Local clients require Python and the installed implicit-ai package with implicit-mcp on PATH. No credentials or remote service are needed for local stdio MCP.

Add the repository marketplace in a supported client with `codex plugin marketplace add zeitcow/implicit-core --ref main`. Source/schema and installed-wheel stdio validation cover the local package; actual desktop installation and hosted ChatGPT connectivity remain not yet verified.

The current [official packaging guidance](https://developers.openai.com/plugins/build/plugins) distinguishes repository marketplaces from the universal public directory. The [submission process](https://developers.openai.com/plugins/deploy/submission) requires developer-dashboard access. MCP review requires a real server connection/domain verification, website/support/privacy/terms URLs, review cases and a demo recording. This release supplies local stdio MCP and does not fabricate a server ID or hosted endpoint. Owner action and platform review remain necessary before directory acceptance; source publication is not marketplace availability.
