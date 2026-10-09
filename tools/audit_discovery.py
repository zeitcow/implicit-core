"""Offline checks for crawlable documentation and real navigation targets."""

import json
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.canonical = None
        self.description = None
        self.headings = 0
        self.has_main = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            self.ids.add(values["id"])
        if tag == "a":
            if values.get("name"):
                self.ids.add(values["name"])
            self.links.append(values.get("href", ""))
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical = values["href"]
        if tag == "meta" and values.get("name") == "description":
            self.description = values.get("content")
        if tag == "h1":
            self.headings += 1
        if tag == "main":
            self.has_main = True


def audit():
    pages = {}
    for path in SITE.glob("*.html"):
        page = Page()
        page.feed(path.read_text(encoding="utf-8"))
        assert page.headings == 1 and page.has_main, path.name
        assert page.canonical and page.description, path.name
        pages[path.resolve()] = page
    links = 0
    failures = []
    for path, page in pages.items():
        for link in page.links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                continue
            links += 1
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            if not target.is_relative_to(SITE.resolve()) or not target.is_file():
                failures.append([path.name, link, "missing or outside site"])
            elif parts.fragment and target in pages and unquote(parts.fragment) not in pages[target].ids:
                failures.append([path.name, link, "missing heading anchor"])
    assert not failures, failures
    sitemap = ET.parse(SITE / "sitemap.xml")
    urls = {node.text for node in sitemap.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")}
    assert urls == {page.canonical for page in pages.values()}
    llms = (SITE / "llms.txt").read_text(encoding="utf-8")
    assert "pip install implicit-ai" in llms and "not RAM" in llms
    assert all(value in llms for value in ["155/155", "93.88%", "94.40%", "99.55%"])
    assert "measured latency tradeoffs" in llms
    assert "serialized/materialized" in llms
    print(
        json.dumps(
            {
                "status": "PASS",
                "html_pages": len(pages),
                "internal_links": links,
                "canonical_sitemap_match": True,
                "broken_links": failures,
                "scope": "Offline HTML navigation/anchors, headings, canonical sitemap, retrieval summary; not indexing",
            }
        )
    )


if __name__ == "__main__":
    audit()
