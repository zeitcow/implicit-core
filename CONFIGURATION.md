# Configuration

Core requires no environment variables, API keys, cloud service or hidden home-directory configuration.

Implicit() uses in-memory LocalTransport. Implicit(database="sessions.db") explicitly chooses a durable journal. Pass a LocalTransport/Engine with ResidencyCache to control capacity, or opt into content storage through Engine configuration. Typed signatures live in implicit.sdk, implicit.engine and implicit.residency.

ExploreConfig(episodes=..., seed=..., candidate_pool=...) controls bounded execution. Your Universe proposes experiences; default selection preserves order. candidate_pool=1 directly schedules the first proposal. Record source/agent versions and seed for reproduction.

CLI run defaults to eight episodes, seed zero and implicit.db in the working directory. Supply --database to choose storage. MCP accepts --help/--version, uses stdio/memory, and fixes limits at 16 universes, 64 addressed experiences, 1,000,000 possible coordinates/universe, 65,536 bytes/frame and two small resource kinds. It opens no listener and accepts no filesystem configuration.
