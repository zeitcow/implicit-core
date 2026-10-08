# Troubleshooting

For missing commands, activate the environment holding the wheel and run python -m pip show implicit-ai, implicit --version and implicit doctor. Avoid the unrelated implicit distribution.

Missing resources and cyclic dependencies are adapter contract failures: implement load/dependencies and immutable versions. Do not patch Core for ordinary integration.

Version mismatches and corrupt journals fail closed. Preserve files and investigate identity/checksum mismatches. Do not discard user state to silence errors. Resume requires the journaled agent version and compatible environment. Reconcile interrupted effects before explicitly authorizing abandon/retry.

MCP waits for initialize and notifications/initialized. tools/list discovers eight tools. Address before materializing. Unknown handles/resources, booleans as integers, extra arguments and exceeded capacities return sanitized errors. Restart resets only synthetic memory; oversized frames close the server. It cannot inspect arbitrary journals.

Cache capacity is not a limit on active dependency closures or RAM. Use admission limits and measure your working set. The public toy cannot establish the private 155-case result; see BENCHMARKS.md.
