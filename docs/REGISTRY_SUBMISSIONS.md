# Technical registry readiness

Reviewed 2026-10-08. Canonical install: `pip install implicit-ai`. Listings remain independent of package publication.

| Candidate | Audience / authority | Submission, cost and requirements | Implicit decision |
| --- | --- | --- | --- |
| PyPI | Python developers; official package index | Existing stable package; free index, existing project ownership | LIVE 1.0.0 |
| GitHub repository and topics | Developers; authoritative source | Project-owned metadata/source, existing authentication | LIVE |
| Official MCP Registry | MCP clients; protocol-maintained metadata registry | Free metadata publication; namespace authentication and package ownership verification | PREPARED; PyPI prerequisite missing |
| OpenAI Plugins Directory | ChatGPT/Codex users; official platform | Verified owner identity, portal access and review; new terms require owner acceptance | Separate skills-only package PREPARED; no acceptance claimed |
| Awesome MCP Servers | Developers; maintained community source list | GitHub PR; public installable server, accurate categorized entry, maintainer review | SUBMITTED [PR #16015](https://github.com/punkpeye/awesome-mcp-servers/pull/16015); acceptance pending |
| Smithery | MCP developers; third-party directory | Current publisher/account and hosting requirements must be verified in its portal | DEFERRED; published hosted connection is not available |
| Zenodo | Research/software citations; archival repository | Owner login, license/identity/terms review and deposition | PREPARED recommendation; no DOI created |

Sources: [official MCP publishing](https://modelcontextprotocol.io/registry/quickstart), [package ownership rules](https://modelcontextprotocol.io/registry/package-types), [OpenAI submission](https://developers.openai.com/plugins/deploy/submission), [community contribution rules](https://github.com/punkpeye/awesome-mcp-servers/blob/main/CONTRIBUTING.md), [citation/archive guidance](https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content).

## Official MCP Registry prerequisite

PyPI-based registration verifies the published package description contains `mcp-name: io.github.zeitcow/implicit-core`. The immutable published 1.0.0 README lacks that marker. Changing repository Markdown does not change PyPI's release description.

Prepared [server manifest](../mcp/server.prepared.json) matches the current schema. Schema validation is not successful ownership verification or publication. Its package/console executable mapping must be confirmed in the publisher/client rehearsal; the supported local launch is `implicit-mcp`, while the package name is `implicit-ai`.

Exact next steps for the next properly versioned package release, if the owner chooses registry publication:

1. Include `<!-- mcp-name: io.github.zeitcow/implicit-core -->` in the package README.
2. Apply ordinary release/versioning verification; update both manifest versions to that release. Do not replace 1.0.0 artifacts or publish merely to decorate metadata.
3. Verify the marker in the live PyPI JSON description.
4. Install the official mcp-publisher CLI, validate the manifest and authenticate the zeitcow namespace through the current supported GitHub flow.
5. Confirm that the client launches `implicit-mcp` from `implicit-ai`, publish, and verify the returned registry record before labeling SUBMITTED/LIVE.

MCPB or OCI packaging could provide another route but is not asserted to exist and is not a reason to expand frozen Core.

## Community submission

Submitted for maintainer review in [PR #16015](https://github.com/punkpeye/awesome-mcp-servers/pull/16015). The entry accurately scopes the server to synthetic local state. Submission is not acceptance.

Concise entry:

`[zeitcow/implicit-core](https://github.com/zeitcow/implicit-core) - Python stdio MCP for bounded synthetic experience addressing, selective state materialization, provenance and fixed benchmark/adapter rehearsal. Real environment adapters use the SDK.`

Place it in the relevant developer-tools category in alphabetical order, preserve the repository's entry conventions, disclose the limited synthetic scope in the PR, and wait for maintainer review. No paid placement, bulk submissions or endorsements are involved.
