"""Rebuild crawler-friendly static docs after approving a canonical URL."""
from pathlib import Path
import argparse
import html
import json
import re
from urllib.parse import urlparse

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
DOCS = ['README.md','QUICKSTART.md','INSTALL.md','ARCHITECTURE.md','ADAPTERS.md','CONFIGURATION.md','TROUBLESHOOTING.md','BENCHMARKS.md','SECURITY.md','CONTRIBUTING.md','CHANGELOG.md','AGENTS.md','MCP.md','PLUGIN_READINESS.md','LICENSING_REVIEW.md','AI_DISCOVERABILITY.md','AGENT_INTEGRATION_BENCHMARK.md','docs/FAQ.md','docs/AGENT_INTEGRATION.md','docs/RELEASE_PLAN.md','docs/LAUNCH_ASSETS.md']


def build(canonical):
    parsed = urlparse(canonical)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.query or parsed.fragment:
        raise ValueError('canonical must be a proposed HTTPS base URL')
    canonical = canonical.rstrip('/')+'/'
    target=ROOT/'site'
    target.mkdir(exist_ok=True)
    pages={n:('index.html' if n=='README.md' else Path(n).stem.lower()+'.html') for n in DOCS}
    parser=MarkdownIt('commonmark', {'html':False}).enable('table')
    style='body{max-width:980px;margin:3rem auto;padding:0 1.5rem;font:18px/1.6 system-ui;color:#19282c;background:#f8fbfa}nav{display:flex;gap:1rem;flex-wrap:wrap}a{color:#00675d}pre{overflow:auto;background:#e9efed;padding:1rem;border-radius:8px}h1{font-size:2.8rem;line-height:1.2}h2{margin-top:2rem}table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:.5rem;border-bottom:1px solid #b7cbc5}footer{margin-top:3rem;border-top:1px solid #b7cbc5}'
    nav=' '.join(f'<a href="{pages[n]}">{Path(n).stem.title()}</a>' for n in ['README.md','INSTALL.md','BENCHMARKS.md','ARCHITECTURE.md','MCP.md','docs/FAQ.md'])
    for name, filename in pages.items():
        text=(ROOT/name).read_text(encoding='utf-8')
        title=text.splitlines()[0].lstrip('# ')
        content=parser.render(text)
        # Markdown links refer to the complete mirrored source tree from this flat HTML directory.
        def rewrite_link(match):
            from posixpath import normpath
            target_link = match[1]
            path, sep, fragment = target_link.partition('#')
            resolved = normpath((Path(name).parent / path).as_posix())
            return 'href="'+pages.get(resolved, 'markdown/'+resolved)+(sep+fragment if sep else '')+'"'
        content=re.sub(r'href="(?!https?://|#)([^\"]+)"',rewrite_link,content)
        metadata={'@context':'https://schema.org','@type':'SoftwareApplication','name':'Implicit','description':'The experience layer for AI agents: selective environment state materialization','softwareVersion':'1.0.0','applicationCategory':'DeveloperApplication','operatingSystem':'Python 3.11+','url':canonical+filename}
        doc=f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} | Implicit</title><meta name="description" content="Implicit experience virtualization: {html.escape(title)}"><link rel="canonical" href="{canonical+filename}"><style>{style}</style><script type="application/ld+json">{json.dumps(metadata)}</script></head><body><nav aria-label="Documentation">{nav}</nav><main>{content}</main><footer>Implicit Core 1.0.0 — stable release. <a href="markdown/{name}">Source Markdown</a>. Apache-2.0.</footer></body></html>\n'
        (target/filename).write_text(doc,encoding='utf-8',newline='\n')
        mirror=target/'markdown'/name
        mirror.parent.mkdir(parents=True,exist_ok=True)
        mirror.write_text(text,encoding='utf-8',newline='\n')
    for name in ['LICENSE','NOTICE','CITATION.cff','benchmarks/rc1-summary.json']:
        mirror=target/'markdown'/name
        mirror.parent.mkdir(parents=True,exist_ok=True)
        mirror.write_bytes((ROOT/name).read_bytes())
    robots='User-agent: OAI-SearchBot\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\nUser-agent: *\nAllow: /\n\nSitemap: '+canonical+'sitemap.xml\n'
    sitemap='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+canonical+p+'</loc></url>' for p in sorted(pages.values()))+'</urlset>\n'
    llms='# Implicit\n\n> The experience layer for AI agents. Stable 1.0.0 release. Install with pip install implicit-ai.\n\n'+'\n'.join(f'- [{Path(n).stem}]({canonical}markdown/{n})' for n in DOCS)+'\n'
    full='\n\n'.join((ROOT/n).read_text(encoding='utf-8') for n in DOCS)+'\n'
    for directory in [ROOT,target]:
        for name,text in [('robots.txt',robots),('sitemap.xml',sitemap),('llms.txt',llms),('llms-full.txt',full)]:
            (directory/name).write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--canonical',required=True)
    build(ap.parse_args().canonical)
