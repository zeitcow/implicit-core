# Quickstart

Install with `pip install implicit-ai` in a fresh environment (see INSTALL.md), then run:

```console
implicit --version
implicit demo
implicit benchmark
python -I examples/core_adapters.py
```

The fixed public toy prints serialized bytes, resource counts, semantic equivalence, seed, provenance and Implicit pipeline time. It does not reproduce the private RC population.

To try durable execution in your chosen working directory:

```console
implicit run --episodes 3 --seed 123 --database "my sessions.db"
```

Output prints a session ID, rewards and metrics. The toy agent is deliberately incomplete on regulated shipping, so some rewards may be zero. This is expected behavior. Replace SESSION_ID with the printed ID:

```console
implicit inspect SESSION_ID --database "my sessions.db"
```

Journals may contain application data. Close all owners, back up files, then explicitly remove only your chosen journal and its SQLite/lease companions to reset. See SECURITY.md.

Start local MCP with `implicit-mcp`; it waits for the client's stdio handshake. Exit/reset discards synthetic memory. See MCP.md for configurations and workflow.
