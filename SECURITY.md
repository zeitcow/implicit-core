# Security and privacy

Local Core uses Python standard-library code and has zero third-party runtime dependencies. There is no telemetry, outbound network client or paid inference. Demo, benchmark and synthetic workloads are exercised with network sockets disabled. Installing a wheel with `--no-index` is network-silent; ordinary pip installation, optional tools or external adapters may use networks under the caller's control.

MemoryStore persists nothing after process exit. SQLite journals persist at the configured database path, including manifest identity, version/strategy metadata, addresses, instructions/probes, executions, verification, resource hashes, mutations and metrics. Journals have no automatic retention expiry. Opt-in DirectoryContentStore retains exact canonical resource/artifact bytes in its explicit directory indefinitely. Compiled indexes contain source records. Uninstall leaves these files intact. Close all owners and back up data before explicitly clearing the selected database, companions and content/index directories.

Use a trusted private storage directory with OS ACLs appropriate for your application. Core does not encrypt data at rest or install OS access controls. It refuses final-path symlinks for journals, leases and content files/directories and validates content digest syntax. An adversary controlling parent directories, replacing paths concurrently or rewriting checksums is outside the trusted-local-filesystem model. Python adapters are trusted executable code, not sandboxed plugins. Logical addresses and resource keys are encoded identifiers and never implicitly become filesystem paths.

Canonical serialization rejects nonfinite values and opaque handles. Resource cycles fail. Hash checks detect corrupted content, index rows and journals; recovery rejects missing/truncated records and incompatible identities. Cache capacity limits retained cache bytes; dependency closure/current state and very large adapter values require caller admission limits. Extremely large, recursive or malicious input can exhaust resources; run untrusted input in an application-managed isolated process with quotas. No unbounded concurrency or security certification is claimed.

Core error events retain error category, stage and status, excluding exception text. CompletionTransaction rejects named credential/reasoning fields and the configured provider key if present. This is not universal secret detection: adapters must omit credentials, private reasoning, hidden evaluator text and gold data from all public records. Core journals can contain business data by design. `inspect`, adapter logs and debug tracebacks can expose it. No debug-mode uploads exist.

Threat review covers path traversal, serialized-state corruption, symlinks, content races, package leakage, temporary-file publication, telemetry/network silence, log injection and cache contamination. The preparation audit records coverage and limitations. Report suspected defects privately to the repository owner; do not put secrets in issues. Dependency advisory checks cannot certify the Python interpreter or OS.

## MCP permissions and data

The local MCP child process communicates through stdin/stdout, opens no sockets, and persists no data. It accepts bounded synthetic coordinates/handles and two fixed resource names. It cannot run shell commands, import supplied code, execute supplied agents, read arbitrary files or inspect existing journals. Paging changes memory only. Benchmark and contract validation use fixed fixtures. Clients may retain returned JSON/provenance in their logs.

No credentials are needed for a pipe owned by the launching user. The trust boundary is that user/process and client; this is not a multi-tenant service. Errors omit submitted values and tracebacks. Restart clears synthetic memory only; SDK journals remain. Caps bound MCP, not arbitrary SDK inputs.

Report vulnerabilities through [GitHub private vulnerability reporting](https://github.com/zeitcow/implicit-core/security/advisories/new). Keep credentials and application data out of public issues. No support email, SLA or security certification is fabricated.
