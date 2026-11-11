#!/usr/bin/env python3
"""Refresh the <script id="scholar-data"> block in index.html from Google Scholar.
Usage: python update_scholar.py [path/to/index.html]
Exits non-zero (leaving index.html untouched) if Scholar can't be parsed."""
import html, json, re, sys, datetime
import requests

USER = "3N7SxOkAAAAJ"
# key -> substring of the paper title (lower-case) as it appears on Scholar
MATCH = {
    "jacs": "platinum graphene catalytic condenser",
    "acscat": "olefin polymerization",
    "esnt": "pd-cha",
    "rce": "methane",
}

path = sys.argv[1] if len(sys.argv) > 1 else "index.html"
page = open(path, encoding="utf-8").read()
m = re.search(r'(<script id="scholar-data" type="application/json">)(.*?)(</script>)', page, re.S)
if not m:
    sys.exit("scholar-data block not found")
data = json.loads(m.group(2))

import os
key = os.environ.get("SERPAPI_KEY")
if not key:
    sys.exit("SERPAPI_KEY is not set (add it as a GitHub repo secret).")
r = requests.get("https://serpapi.com/search.json",
                 params={"engine": "google_scholar_author", "author_id": USER,
                         "hl": "en", "num": 100, "api_key": key}, timeout=60)
r.raise_for_status()
j = r.json()
if "articles" not in j:
    sys.exit("Unexpected SerpAPI response: " + str(j)[:300])
counts = {a["title"].lower(): int((a.get("cited_by") or {}).get("value") or 0) for a in j["articles"]}

for p in data["papers"]:
    needle = MATCH.get(p["key"])
    hit = [n for title, n in counts.items() if needle and needle in title]
    if hit:
        p["n"] = max(hit)

try:
    data["total"] = int(j["cited_by"]["table"][0]["citations"]["all"])
except Exception:
    data["total"] = sum(counts.values())
data["updated"] = datetime.date.today().strftime("%B %d, %Y")

new = m.group(1) + json.dumps(data, ensure_ascii=False) + m.group(3)
open(path, "w", encoding="utf-8").write(page[:m.start()] + new + page[m.end():])
print("Updated:", data["total"], data["updated"])
