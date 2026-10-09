# Implicit Integration plugin

Guide adapter integration into an existing Python agent environment and compare eager and selective materialization with measured evidence. This skill requires a local coding environment. Install Implicit separately with `pip install implicit-ai` in an isolated environment; verify version 1.0.0.

Add this public repository marketplace and install the skill:

```console
codex plugin marketplace add zeitcow/implicit-core --ref main
codex plugin add implicit-integration@implicit-core
```

Start a new Codex chat after installation. A first prompt is:

> Use $implicit-integration to inspect my agent environment and propose page boundaries, source versions and an eager versus selective verification plan. Explain the plan before editing files.

The package contains one skill and two public reference documents. It has no bundled MCP server, hooks, app credentials or telemetry. Adapter code runs in the caller's project. Preserve the user's agent/framework and exclude secrets, private reasoning and evaluator answers from journals.

For the separate bounded synthetic stdio MCP server, install `implicit-ai` and run `implicit-mcp`; see [MCP setup](https://zeitcow.github.io/implicit-core/mcp_quickstart.html). The skill does not turn that server into a custom-code executor.

Repo marketplace availability is independent of OpenAI's reviewed Plugins Directory. No public directory approval is claimed. The released skill ZIP is also suitable for the separate owner-authenticated submission workflow, subject to the portal's current eligibility and checks.

This plugin and its included references are Apache-2.0 licensed; see LICENSE. Source and measured scope: https://github.com/zeitcow/implicit-core and https://zeitcow.github.io/implicit-core/.
