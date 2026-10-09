"""Build crawlable public docs from their Markdown source."""

import argparse
import html
import json
import re
from pathlib import Path
from posixpath import normpath
from urllib.parse import urlparse

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    "README.md",
    "QUICKSTART.md",
    "INSTALL.md",
    "ARCHITECTURE.md",
    "ADAPTERS.md",
    "CONFIGURATION.md",
    "TROUBLESHOOTING.md",
    "BENCHMARKS.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "AGENTS.md",
    "MCP.md",
    "PLUGIN_READINESS.md",
    "LICENSING_REVIEW.md",
    "AI_DISCOVERABILITY.md",
    "AGENT_INTEGRATION_BENCHMARK.md",
    "docs/FAQ.md",
    "docs/AGENT_INTEGRATION.md",
    "docs/RELEASE_PLAN.md",
    "docs/LAUNCH_ASSETS.md",
    "docs/MCP_QUICKSTART.md",
    "docs/ECOSYSTEMS.md",
    "docs/REGISTRY_SUBMISSIONS.md",
    "docs/CITING.md",
    "docs/ADOPTION.md",
    "ADOPTION_BASELINE.md",
]
DESCRIPTIONS = {
    "README.md": "Implicit is the experience layer for AI agents. Virtualize large environments and materialize only required state. Install implicit-ai.",
    "BENCHMARKS.md": "Implicit rc1 methodology and results: 155/155 equivalent cases; 93.88% aggregate, 94.40% mean and 99.55% median retained serialized/materialized-state reduction.",
    "INSTALL.md": "Install Implicit Core 1.0.0 from PyPI with pip install implicit-ai. Python 3.11+, isolated environment, zero runtime dependencies.",
    "docs/MCP_QUICKSTART.md": "Connect a coding agent to Implicit's eight bounded local MCP tools. PyPI installation and current Codex, Claude Code, VS Code and Cursor configuration.",
    "docs/AGENT_INTEGRATION.md": "Keep your agent and native evaluator. Build an Implicit adapter and compare eager versus selective state with equivalence, bytes and complete latency.",
}


def build(canonical):
    parsed = urlparse(canonical)
    if parsed.scheme != "https" or not parsed.hostname or parsed.query or parsed.fragment:
        raise ValueError("canonical must be an HTTPS base URL")
    canonical = canonical.rstrip("/") + "/"
    target = ROOT / "site"
    target.mkdir(exist_ok=True)
    pages = {n: ("index.html" if n == "README.md" else Path(n).stem.lower() + ".html") for n in DOCS}
    if len(set(pages.values())) != len(pages):
        raise ValueError("Duplicate generated page names")
    parser = MarkdownIt("commonmark", {"html": False}).enable("table")
    style = (
        "body{max-width:980px;margin:2rem auto;padding:0 1.5rem;font:18px/1.6 system-ui;color:#19282c;background:#f8fbfa}"
        "nav{display:flex;gap:.8rem;flex-wrap:wrap;font-size:16px}a{color:#00675d}a:hover{text-decoration-thickness:2px}"
        "pre{overflow:auto;background:#e9efed;padding:1rem;border-radius:8px}h1{font-size:2.8rem;line-height:1.2}"
        "h2{margin-top:2rem}table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:.5rem;border-bottom:1px solid #b7cbc5}"
        "footer{margin-top:3rem;border-top:1px solid #b7cbc5;font-size:16px}@media(max-width:600px){body{font-size:16px}h1{font-size:2.2rem}}"
    )
    nav = " ".join(
        f'<a href="{pages[n]}">{label}</a>'
        for n, label in [
            ("README.md", "Implicit"),
            ("QUICKSTART.md", "Start"),
            ("ADAPTERS.md", "Adapters"),
            ("BENCHMARKS.md", "Evidence"),
            ("docs/MCP_QUICKSTART.md", "MCP"),
            ("docs/FAQ.md", "FAQ"),
        ]
    )
    nav += ' <a href="https://github.com/zeitcow/implicit-core">GitHub</a> <a href="https://pypi.org/project/implicit-ai/">PyPI</a>'
    software = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "Implicit",
        "description": DESCRIPTIONS["README.md"],
        "softwareVersion": "1.0.0",
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Python 3.11+",
        "license": "https://www.apache.org/licenses/LICENSE-2.0",
        "url": canonical,
    }
    for name, filename in pages.items():
        text = (ROOT / name).read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ")
        description = DESCRIPTIONS.get(
            name,
            title
            + " for Implicit Core 1.0.0: experience virtualization, selective state and measured integration.",
        )
        tokens = parser.parse(text)
        slugs = {}
        for i, token in enumerate(tokens):
            if token.type == "heading_open":
                label = tokens[i + 1].content
                base = re.sub(r"[^\w\s-]", "", label.lower())
                base = re.sub(r"\s+", "-", base)
                repeat = slugs.get(base, 0)
                slugs[base] = repeat + 1
                token.attrSet("id", base + (f"-{repeat}" if repeat else ""))
        content = parser.renderer.render(tokens, parser.options, {})

        def rewrite_link(match):
            link = html.unescape(match[1])
            if urlparse(link).scheme or link.startswith(("#", "//")):
                return match[0]
            path, sep, fragment = link.partition("#")
            resolved = normpath((Path(name).parent / path).as_posix())
            url = pages.get(resolved, "markdown/" + resolved) + (sep + fragment if sep else "")
            return 'href="' + html.escape(url, quote=True) + '"'

        content = re.sub(r'href="([^"]+)"', rewrite_link, content)
        url = canonical if name == "README.md" else canonical + filename
        metadata = (
            software
            if name == "README.md"
            else {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": title,
                "url": url,
                "description": description,
                "about": {"@type": "SoftwareApplication", "name": "Implicit", "softwareVersion": "1.0.0"},
            }
        )
        escaped_title = html.escape(title + " | Implicit")
        escaped_description = html.escape(description, quote=True)
        doc = (
            f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escaped_title}</title><meta name="description" content="{escaped_description}"><link rel="canonical" href="{url}">'
            f'<meta property="og:title" content="{escaped_title}"><meta property="og:description" content="{escaped_description}">'
            f'<meta property="og:type" content="website"><meta property="og:site_name" content="Implicit"><meta property="og:url" content="{url}">'
            f'<style>{style}</style><script type="application/ld+json">{json.dumps(metadata)}</script></head>'
            f'<body><nav aria-label="Documentation">{nav}</nav><main>{content}</main>'
            f'<footer>Implicit Core 1.0.0. <a href="markdown/{name}">Source Markdown</a>. Apache-2.0.</footer></body></html>\n'
        )
        (target / filename).write_text(doc, encoding="utf-8", newline="\n")
        mirror = target / "markdown" / name
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_text(text, encoding="utf-8", newline="\n")
    assets = [
        "LICENSE",
        "NOTICE",
        "CITATION.cff",
        "ADOPTION_METRICS.json",
        "benchmarks/rc1-summary.json",
        "tools/adoption_snapshot.py",
        "mcp/server.prepared.json",
    ]
    assets += [p.relative_to(ROOT).as_posix() for p in (ROOT / "examples").glob("*.py")]
    for name in assets:
        mirror = target / "markdown" / name
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_bytes((ROOT / name).read_bytes())
    robots = (
        "# Advisory copy: crawlers read robots.txt at the origin root.\n"
        "User-agent: OAI-SearchBot\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\nUser-agent: *\nAllow: /\n\nSitemap: "
        + canonical
        + "sitemap.xml\n"
    )
    urls = [canonical if p == "index.html" else canonical + p for p in sorted(pages.values())]
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join("<url><loc>" + html.escape(u) + "</loc></url>" for u in urls)
        + "</urlset>\n"
    )
    llms = (
        "# Implicit\n\n> The experience layer for AI agents. Virtualize large environments; materialize required state.\n\n"
        "Stable 1.0.0. Python 3.11+. Install: pip install implicit-ai. Import: implicit. Use isolation to avoid the unrelated implicit distribution.\n\n"
        "Use for large separable state, versioned experiences and durable evidence; measure overhead for small/already lazy state. Keep the existing agent/framework/evaluator; adapters live in the application.\n\n"
        "Historical rc1: 155/155 equivalent cases, 93.88% aggregate/94.40% mean/99.55% median retained serialized/materialized-state reduction. Bytes are not RAM. See the benchmark methodology and results for measured latency tradeoffs. Restricted native replay assets are not shipped.\n\n"
        "MCP is local stdio with eight bounded synthetic tools. Custom adapters use SDK tests. Repository plugin source is separate from public directory acceptance. No hosted endpoint is claimed.\n\n## Start here\n\n"
    )
    primary = [
        "QUICKSTART.md",
        "INSTALL.md",
        "ADAPTERS.md",
        "docs/AGENT_INTEGRATION.md",
        "BENCHMARKS.md",
        "docs/MCP_QUICKSTART.md",
        "SECURITY.md",
        "docs/ECOSYSTEMS.md",
        "docs/CITING.md",
    ]
    llms += "\n".join(
        f"- [{Path(n).stem.replace('_', ' ').title()}]({canonical}markdown/{n})" for n in primary
    )
    llms += "\n\n## Further reference\n\n" + "\n".join(
        f"- [{Path(n).stem}]({canonical}markdown/{n})" for n in DOCS if n not in primary
    )
    llms += "\n\n- [GitHub](https://github.com/zeitcow/implicit-core)\n- [PyPI](https://pypi.org/project/implicit-ai/)\n"
    full = "\n\n".join((ROOT / n).read_text(encoding="utf-8") for n in DOCS) + "\n"
    for directory in [ROOT, target]:
        for name, value in [
            ("robots.txt", robots),
            ("sitemap.xml", sitemap),
            ("llms.txt", llms),
            ("llms-full.txt", full),
        ]:
            (directory / name).write_text(value, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--canonical", required=True)
    build(ap.parse_args().canonical)
