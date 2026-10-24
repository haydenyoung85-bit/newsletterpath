#!/usr/bin/env python3
"""Weekly re-check of every source page. NOT scheduled; run by hand:
    python3 scripts/update_check.py --init     # (re)write the baseline from the live pages
    python3 scripts/update_check.py            # compare live pages with the baseline, log differences
For each source URL it renders the page (system Chrome via Playwright), extracts the money amounts, percentages and
"N subscribers/contacts/members" phrases, and compares that token set with data/baseline.json.
Differences are appended to data/changes.json (shown on /changes) and logs/update_<date>.log.  It never edits platforms.json
or programs.json: a human re-reads the page, updates the data, bumps last_verified, and rebuilds.
Pages that sit behind a bot challenge (HTTP 403 / "Just a moment") are reported as BLOCKED and skipped."""
import json, re, sys, pathlib, datetime, time
from playwright.sync_api import sync_playwright
R = pathlib.Path(__file__).resolve().parent.parent
CHROME = "/usr/bin/google-chrome"
TOK = [r"\$\s?\d[\d,]*(?:\.\d+)?", r"\d[\d,]*(?:\.\d+)?\s?%", r"\d[\d,]{2,}\+?\s+(?:active\s+)?(?:subscribers|contacts|members)"]
def tokens(text):
    out = set()
    for rx in TOK:
        for m in re.findall(rx, text, flags=re.I): out.add(re.sub(r"\s+", " ", m.strip().lower()))
    return sorted(out)
def items():
    seen = {}
    for p in json.load(open(R / "data/platforms.json"))["platforms"]:
        for u in p["sources"] + ([p["fee_src"]] if p.get("fee_src") else []): seen.setdefault(u, p["name"])
    for p in json.load(open(R / "data/programs.json"))["programs"]:
        for u in p["sources"]: seen.setdefault(u, p["name"])
    return seen
def fetch(pg, u):
    try:
        r = pg.goto(u, wait_until="domcontentloaded", timeout=45000)
        try: pg.wait_for_load_state("networkidle", timeout=15000)
        except Exception: pass
        pg.wait_for_timeout(1500)
        t = pg.inner_text("body")
        if (r and r.status in (403, 429)) or "just a moment" in pg.title().lower(): return "BLOCKED", ""
        if r and r.status >= 400: return f"HTTP {r.status}", ""
        return "OK", t
    except Exception as e: return "ERROR " + str(e)[:80], ""
def main():
    init = "--init" in sys.argv
    today = datetime.date.today().isoformat()
    bpath = R / "data/baseline.json"
    base = json.load(open(bpath)) if bpath.exists() and not init else {}
    new = {}; log = []; changes = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"]); pg = b.new_page()
        for u, name in items().items():
            st, text = fetch(pg, u)
            tk = tokens(text) if st == "OK" else None
            new[u] = {"item": name, "status": st, "tokens": tk, "checked": today}
            old = base.get(u)
            if init: log.append(f"INIT   {st:8} {len(tk) if tk is not None else '-':>4} tokens  {u}")
            elif st != "OK": log.append(f"SKIP   {st:8} {name}: {u}")
            elif not old or old.get("tokens") is None: log.append(f"NEW    {name}: no baseline for {u}")
            else:
                add = sorted(set(tk) - set(old["tokens"])); rem = sorted(set(old["tokens"]) - set(tk))
                if add or rem:
                    log.append(f"CHANGE {name}: +{add[:15]} -{rem[:15]} {u}")
                    changes.append({"date": today, "item": name, "field": "figures on source page (review manually)", "old": ", ".join(rem[:12]) or "–", "new": ", ".join(add[:12]) or "–", "url": u})
                else: log.append(f"same   {name}: {u}")
        b.close()
    if init or not bpath.exists():
        # keep earlier good tokens when a page is blocked this time
        json.dump(new, open(bpath, "w"), indent=1)
    elif changes:
        # update baseline tokens only for changed pages so they are not reported twice
        for c in changes: base[c["url"]] = new[c["url"]]
        json.dump(base, open(bpath, "w"), indent=1)
    if changes:
        cp = R / "data/changes.json"; d = json.load(open(cp)); d["entries"] += [{k: v for k, v in c.items() if k != "url"} for c in changes]
        json.dump(d, open(cp, "w"), indent=1)
    (R / "logs").mkdir(exist_ok=True)
    (R / "logs" / f"update_{today}.log").write_text("\n".join(log) + "\n")
    print("\n".join(log)); print(f"\n{len(changes)} changed page(s). " + ("Run scripts/build_site.py and commit." if changes else ""))
main()
