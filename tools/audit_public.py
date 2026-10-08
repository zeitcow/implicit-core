"""Audit exact public export without private repository knowledge or network."""
from pathlib import Path
import ast
import hashlib
import json
import re
import statistics
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def audit():
    manifest = json.loads((ROOT / 'PUBLIC_EXPORT_MANIFEST.json').read_text(encoding='utf-8'))
    expected = {r['path']: r['sha256'] for r in manifest['files']}
    for name, digest in expected.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    excluded = ('allocation.py', '/backends/', '/validation/', '/research/', 'tau3.py', 'semantic_retail.py')
    for p in ROOT.rglob('*'):
        rel = p.relative_to(ROOT).as_posix()
        if not p.is_file() or any(part in {'.git', '.venv', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'dist'} for part in p.parts):
            continue
        assert rel in expected or rel == 'PUBLIC_EXPORT_MANIFEST.json', f'unmanifested file: {rel}'
        assert not any(x in '/'+rel for x in excluded), rel
        text = p.read_text(encoding='utf-8')
        assert not re.search(r'(?:C:\\Users\\|/Users/|/home/)[A-Za-z0-9_]', text, re.I), rel
        assert not re.search(r'(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{25,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)', text), rel
        if rel.startswith('src/') and p.suffix == '.py':
            for node in ast.walk(ast.parse(text)):
                if isinstance(node, ast.ImportFrom):
                    assert not (node.module or '').startswith(('implicit.allocation', 'implicit.search', 'implicit.backends', 'implicit.validation')), rel
                if isinstance(node, ast.Import):
                    assert not any(n.name.split('.')[0] in {'requests', 'httpx', 'socket', 'urllib', 'subprocess'} for n in node.names), rel
    for name in ['README.md', 'BENCHMARKS.md', 'docs/FAQ.md', 'CHANGELOG.md']:
        text = (ROOT/name).read_text(encoding='utf-8')
        assert '0.554' in text and ('RAM' in text or 'memory' in text), name
    for p in [ROOT/'README.md', *ROOT.glob('*.md'), *ROOT.glob('docs/*.md')]:
        for target in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)', p.read_text(encoding='utf-8')):
            if not target.startswith(('https:', 'http:')):
                assert (p.parent/target).exists(), (p.name, target)
    summary = json.loads((ROOT/'benchmarks/rc1-summary.json').read_text(encoding='utf-8'))
    cases = summary['cases']
    eager = sum(c['eager_retained_bytes'] for c in cases)
    lazy = sum(c['implicit_retained_bytes'] for c in cases)
    assert eager == 274839550 and lazy == 16808820 and len(cases) == 155
    assert all(c['equivalent'] for c in cases)
    ratios = [1-c['implicit_retained_bytes']/c['eager_retained_bytes'] for c in cases]
    assert abs(statistics.median(ratios)-summary['headline']['median_reduction']) < 1e-12
    assert abs(statistics.mean(c['latency_delta_seconds'] for c in cases)-0.5538194612941645) < 1e-9
    plugin = json.loads((ROOT/'plugin/plugin.json').read_text(encoding='utf-8'))
    assert plugin['name'] == 'implicit-core'
    compat = json.loads((ROOT/'plugin/.codex-plugin/plugin.json').read_text(encoding='utf-8'))
    for key in ['skills', 'mcpServers']:
        target = compat[key]
        assert target.startswith('./') and '..' not in Path(target).parts
        assert (ROOT/'plugin'/target).exists()
    portable = json.loads((ROOT/'plugin/mcp.json').read_text(encoding='utf-8'))
    assert portable['mcpServers']['implicit'] == {'type':'stdio','command':'implicit-mcp','args':[]}
    ET.parse(ROOT/'site/sitemap.xml')
    for bot in ['OAI-SearchBot', 'PerplexityBot']:
        assert f'User-agent: {bot}\nAllow: /' in (ROOT/'site/robots.txt').read_text(encoding='utf-8')
    for p in (ROOT/'site').glob('*.html'):
        text = p.read_text(encoding='utf-8')
        assert '<main>' in text and '<h1>' in text and 'rel="canonical"' in text
        assert 'application/ld+json' in text and '<script src' not in text
    print(json.dumps({'status':'PASS','manifested_files':len(expected),'scope':'hashes, exact tree, leak patterns, runtime imports, links, benchmark arithmetic, plugin paths, crawler/static HTML; not formal security certification'}))


if __name__ == '__main__':
    audit()
