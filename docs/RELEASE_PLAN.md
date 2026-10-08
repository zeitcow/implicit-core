# Release plan

Implicit Core 1.0.0 is the stable initial release, licensed under Apache-2.0. Public repository: https://github.com/zeitcow/implicit-core. Distribution: implicit-ai; import: implicit. Tag: v1.0.0. Historical v1.0.0rc2 remains unchanged; stable source derives from public RC2 SHA f741c1d07731be15c31f45458894fb49a9d79128. Public history begins with the audited allowlisted export.

Release order: promote validated RC2 with a minimal diff; audit licensed source/artifacts; verify Windows/Linux Python 3.11–3.14 CI; create stable tag/release with checksums; publish exactly implicit-ai==1.0.0 using OIDC Trusted Publishing; verify fresh `pip install implicit-ai`, adapters and local MCP; verify live documentation. Publisher identity: owner zeitcow, repository implicit-core, workflow pypi.yml, environment pypi. No long-lived PyPI token is required.

Benchmark facts refer to the preserved rc1 population: 155/155 equivalent cases, 93.88% aggregate, 94.40% mean and 99.55% median retained serialized/materialized-state reduction, with approximately +0.554 seconds/case mean full-pipeline overhead. Bytes are not RAM. RC2 MCP validation is separate.

Canonical documentation: https://zeitcow.github.io/implicit-core/. PyPI and site availability must be verified at their actual public URLs. The repository documentation and release artifacts remain usable independently.

Plugin source is public. Universal directory submission and hosted connectivity remain unverified and require the current platform review process. No registration, marketplace acceptance or remote endpoint is implied by source publication.
