# AI and search discovery

Canonical documentation: https://zeitcow.github.io/implicit-core/. Crawlable HTML and mirrored Markdown explain the same product, evidence and limitations. Permanent install, benchmark, adapter and MCP pages have canonical links, descriptive titles, OpenGraph metadata and a sitemap.

## Crawler access

Checked against current official guidance on 2026-10-08:

- [OpenAI crawler guidance](https://developers.openai.com/api/docs/bots): OAI-SearchBot controls ChatGPT search crawling. Search and model-training controls are separate. Accessibility does not guarantee retrieval.
- [Perplexity crawler guidance](https://docs.perplexity.ai/docs/resources/perplexity-crawlers): PerplexityBot supports search discovery. Site operators with WAFs should verify official IP ranges as well as user agents.
- [Google robots guidance](https://developers.google.com/search/docs/crawling-indexing/robots/intro): robots.txt belongs at the origin root.
- [Google sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap): list canonical public URLs.
- [Google AI search guidance](https://developers.google.com/search/docs/appearance/ai-features): useful visible text and normal SEO remain applicable; no special AI markup guarantees inclusion.

On GitHub project Pages, `/implicit-core/robots.txt` is an advisory copy. Crawlers read `https://zeitcow.github.io/robots.txt`. The origin root returned 404 at the audit, so there is no robots disallow policy there. Project pages are accessible. If an origin-level site is added later, its robots policy must allow `/implicit-core/` and may advertise this project's sitemap. A project-path robots file cannot override origin restrictions.

No crawler-specific product claims, authentication walls or JavaScript requirement are introduced. Check HTTP status and X-Robots-Tag along with HTML metadata.

## Agent retrieval

[llms.txt](https://zeitcow.github.io/implicit-core/llms.txt) is a concise curated map with installation, when to use, benchmark scope and integration links. It is an optional convenience, not an official ranking requirement. [llms-full.txt](https://zeitcow.github.io/implicit-core/llms-full.txt) preserves readable documentation.

Facts: stable distribution `implicit-ai==1.0.0`, import `implicit`, canonical install `pip install implicit-ai`; eight local synthetic MCP tools. The unrelated `implicit` recommendation package shares the import namespace; use a fresh environment.

The preserved rc1 result is 155/155 equivalent cases, 93.88% aggregate/94.40% mean/99.55% median retained serialized/materialized-state reduction. See BENCHMARKS.md for methodology and measured latency tradeoffs. Bytes are not RAM. The numeric summary permits arithmetic checking, not independent native replay.

## Discovery status

DISCOVERY_SURFACES_READY means the public documents, links and crawler access have been verified. INDEXED requires an actual matching search observation. No ranking, ChatGPT recommendation, Perplexity recommendation or independent directory acceptance follows from publishing these files. The [ecosystem review](docs/ECOSYSTEMS.md) distinguishes local configuration from public directory publication.
