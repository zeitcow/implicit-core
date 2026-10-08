# Public adoption measurement

Implicit has no hidden product telemetry. Measure public aggregate signals and voluntary integration evidence.

The timestamped [baseline](../ADOPTION_BASELINE.md) and [machine-readable snapshot](../ADOPTION_METRICS.json) are observations, not counts of active users. Stars, forks and downloads cannot establish production adoption. Our own installation checks, automation and CI can affect downloads and traffic.

Run the optional measurement tool from a public source checkout:

```console
python tools/adoption_snapshot.py
```

It writes a new timestamped JSON file under `dist/adoption/`; existing snapshots are not overwritten. It fetches GitHub repository counts, release downloads, issue/PR totals, contributor counts and PyPIStats aggregates. It is separate from the SDK and CLI runtime.

GitHub anonymous rate limits may apply. An optional GITHUB_TOKEN can provide project-owner API access; it is never recorded. `--owner-traffic` requests only aggregate views/clones over the API's rolling window. Keep that output private unless the owner chooses to publish it. No visitors, anonymous downloaders or personal identities are inferred.

Unavailable metrics are null with an HTTP status/reason, not zero. Discussions, citations, backlinks, public mentions and search indexing need separate observations. Search indexing and retrieval readiness are independent. [Discovery guidance](../AI_DISCOVERABILITY.md).

For follow-up, preserve weekly snapshots and compare the same windows, noting releases and our own verification activity. Count voluntary public adapter reports, external PRs and reproducible issue reports separately. Capture no private data and send no unsolicited follow-up.
