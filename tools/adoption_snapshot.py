"""Optional public aggregate measurements; never imported by Core."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = "zeitcow/implicit-core"
API = "https://api.github.com"


def request(url: str) -> dict:
    headers = {"User-Agent": "implicit-adoption-snapshot/1.0"}
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith(API + "/"):
        headers["Authorization"] = "Bearer " + token
        headers["Accept"] = "application/vnd.github+json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
            return {"source": url, "http_status": response.status, "data": json.load(response)}
    except urllib.error.HTTPError as exc:
        return {"source": url, "http_status": exc.code, "data": None, "reason": exc.reason}
    except (OSError, ValueError):
        return {
            "source": url,
            "http_status": None,
            "data": None,
            "reason": "Network or JSON response unavailable",
        }


def snapshot(owner_traffic: bool = False) -> dict:
    metrics = {
        "schema": 1,
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repository": REPO,
        "package": "implicit-ai",
        "interpretation": "Aggregate signals, not active users; owner checks and CI may contribute.",
    }
    r = request(API + "/repos/" + REPO)
    data = r.pop("data")
    metrics["github"] = {
        **r,
        **{
            k: data.get(k) if data else None
            for k in [
                "stargazers_count",
                "forks_count",
                "subscribers_count",
                "open_issues_count",
                "has_discussions",
            ]
        },
    }
    r = request(API + "/repos/" + REPO + "/releases?per_page=100")
    data = r.pop("data")
    metrics["releases"] = {
        **r,
        "first_100_releases": [
            {
                "tag": release["tag_name"],
                "downloads": sum(a["download_count"] for a in release["assets"]),
                "assets": [{"name": a["name"], "downloads": a["download_count"]} for a in release["assets"]],
            }
            for release in data
        ]
        if data is not None
        else None,
    }
    for label, query in [
        ("issues_total", "repo:" + REPO + " is:issue"),
        ("pull_requests_total", "repo:" + REPO + " is:pr"),
    ]:
        r = request(API + "/search/issues?" + urllib.parse.urlencode({"q": query, "per_page": 1}))
        data = r.pop("data")
        metrics[label] = {
            **r,
            "count": data["total_count"] if data else None,
            "incomplete_results": data.get("incomplete_results") if data else None,
        }
    count = external = 0
    pages = 0
    reason = None
    while True:
        r = request(API + "/repos/" + REPO + "/contributors?per_page=100&page=" + str(pages + 1))
        data = r["data"]
        if data is None:
            count = external = None
            reason = r.get("reason")
            break
        pages += 1
        count += len(data)
        external += sum(c["login"] != "zeitcow" and c.get("type") != "Bot" for c in data)
        if len(data) < 100:
            break
    metrics["contributors"] = {
        "count": count,
        "external_non_bot_count": external,
        "source": API + "/repos/" + REPO + "/contributors",
        "pages": pages,
        "reason": reason,
        "scope": "Commit authors recognized by GitHub; names are not recorded.",
    }
    metrics["pypi_downloads"] = request("https://pypistats.org/api/packages/implicit-ai/recent")
    for name in ["citations", "backlinks", "public_mentions", "active_users", "search_indexing"]:
        metrics[name] = {"value": None, "reason": "Not measured by this aggregate snapshot"}
    metrics["discussions"] = {
        "count": 0 if metrics["github"]["has_discussions"] is False else None,
        "reason": "Disabled" if metrics["github"]["has_discussions"] is False else "Not queried",
    }
    if owner_traffic:
        for name in ["views", "clones"]:
            r = request(API + "/repos/" + REPO + "/traffic/" + name)
            data = r.pop("data")
            metrics["traffic_" + name] = {
                **r,
                "count": data.get("count") if data else None,
                "uniques": data.get("uniques") if data else None,
                "daily_aggregates": data.get(name) if data else None,
                "scope": "GitHub rolling 14-day window; keep owner output private",
            }
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--owner-traffic", action="store_true")
    args = parser.parse_args()
    result = snapshot(args.owner_traffic)
    output = args.output or Path("dist/adoption") / (
        dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(output.as_posix())


if __name__ == "__main__":
    main()
