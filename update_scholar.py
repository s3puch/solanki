#!/usr/bin/env python3
"""Refresh the <script id="scholar-data"> block in index.html from Google Scholar.
Usage: python update_scholar.py [path/to/index.html]
Exits non-zero (leaving index.html untouched) if Scholar can't be parsed."""
import html, json, re, sys, datetime
import requests

USER = "3N7SxOkAAAAJ"
URL = f"https://scholar.google.com/citations?user={USER}&hl=en&cstart=0&pagesize=100"
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

r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}, timeout=30)
r.raise_for_status()
rows = re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', r.text, re.S)
if not rows:
    sys.exit("No publication rows found (Scholar probably served a CAPTCHA); not updating.")

counts = {}
for row in rows:
    t = re.search(r'class="gsc_a_at"[^>]*>(.*?)</a>', row, re.S)
    c = re.search(r'class="gsc_a_ac[^"]*"[^>]*>(\d*)</a>', row, re.S)
    if t:
        counts[html.unescape(re.sub("<.*?>", "", t.group(1))).lower()] = int(c.group(1) or 0) if c else 0

for p in data["papers"]:
    needle = MATCH.get(p["key"])
    hit = [n for title, n in counts.items() if needle and needle in title]
    if hit:
        p["n"] = max(hit)

tot = re.search(r'Citations</a></td><td class="gsc_rsb_std">(\d+)', r.text)
data["total"] = int(tot.group(1)) if tot else sum(counts.values())
data["updated"] = datetime.date.today().strftime("%B %d, %Y")

new = m.group(1) + json.dumps(data, ensure_ascii=False) + m.group(3)
open(path, "w", encoding="utf-8").write(page[:m.start()] + new + page[m.end():])
print("Updated:", data["total"], data["updated"])
