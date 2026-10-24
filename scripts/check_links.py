#!/usr/bin/env python3
"""Checks every page in docs/ (or a live base URL): HTTP status of every internal and external link, plus title/description/canonical/h1 per page.
Usage: python3 scripts/check_links.py [live_base_url]"""
import sys, re, pathlib, urllib.request, urllib.parse, concurrent.futures as cf, html
R = pathlib.Path(__file__).resolve().parent.parent
live = sys.argv[1].rstrip("/") + "/" if len(sys.argv) > 1 else None
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36"}
PRE = "/newsletterpath/"
def get(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25); return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e: return e.code, ""
    except Exception as e: return str(e)[:60], ""
paths = re.findall(r"<loc>https://[^/]+/newsletterpath/(.*?)</loc>", (R / "docs/sitemap.xml").read_text())
pages = {}
for p in paths:
    if live: pages[p] = get(live + p)[1]
    else: pages[p] = (R / "docs" / p / "index.html" if p else R / "docs/index.html").read_text()
bad = []; ext = {}; internal = set()
for p, h in pages.items():
    t = re.search(r"<title>(.*?)</title>", h); d = re.search(r'name="description" content="(.*?)"', h); c = re.search(r'rel="canonical" href="(.*?)"', h)
    n1 = len(re.findall(r"<h1[ >]", h))
    ok = bool(t and d and c) and n1 == 1 and 20 < len(html.unescape(t.group(1))) <= 72 and 70 <= len(html.unescape(d.group(1))) <= 175
    print(("OK  " if ok else "WARN"), p or "/", "| title", len(t.group(1)) if t else None, "| desc", len(d.group(1)) if d else None, "| h1", n1, "| canon", c.group(1) if c else None)
    if not ok: bad.append(("meta", p))
    for href in re.findall(r'(?:<a [^>]*href|<script[^>]*src|<link rel="stylesheet" href)="([^"#]+)(?:#[^"]*)?"', h):
        if href.startswith("data:") : continue
        if href.startswith("http"): ext.setdefault(href, []).append(p)
        elif href.startswith("/"): internal.add(href)
def chk_int(href):
    path = href[len(PRE):] if href.startswith(PRE) else None
    if path is None: return href, "outside-base"
    if live: return href, get(live + path)[0]
    f = R / "docs" / path
    if f.is_dir(): f = f / "index.html"
    return href, 200 if f.exists() else 404
with cf.ThreadPoolExecutor(8) as ex:
    ri = list(ex.map(chk_int, sorted(internal)))
    re_ = list(ex.map(lambda u: (u, get(u)[0]), sorted(ext)))
print("\nINTERNAL", len(ri), "checked;", "bad:", [x for x in ri if x[1] != 200])
print("EXTERNAL", len(re_), "checked")
for u, s in re_:
    if s != 200: print("  ", s, u, "<-", ext[u][:2])
# anchors
for p, h in pages.items():
    for a in re.findall(r'href="(/newsletterpath/[^"]*#([^"]+))"', h):
        tgt = a[0].split("#")[0][len(PRE):]; th = pages.get(tgt)
        if th is not None and f'id="{a[1]}"' not in th: print("MISSING ANCHOR", a[0], "on", p)
