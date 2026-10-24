#!/usr/bin/env python3
"""Screenshots every page at phone (390x844) and desktop (1366x900); reports horizontal overflow, page height, console errors.
Usage: python3 scripts/screenshots.py [base_url]   (default: local server on docs/ via a /newsletterpath symlink)"""
import sys, pathlib, subprocess, tempfile, os, time, re, json
from playwright.sync_api import sync_playwright
R = pathlib.Path(__file__).resolve().parent.parent
OUT = R / "shots"; OUT.mkdir(exist_ok=True)
base = sys.argv[1] if len(sys.argv) > 1 else None
srv = None
if not base:
    tmp = tempfile.mkdtemp(); os.symlink(R / "docs", pathlib.Path(tmp) / "newsletterpath")
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "18431", "-d", tmp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1); base = "http://localhost:18431/newsletterpath/"
paths = re.findall(r"<loc>https://[^/]+/newsletterpath/(.*?)</loc>", (R / "docs/sitemap.xml").read_text())
res = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for name, vp, dsf, mob in (("phone", {"width": 390, "height": 844}, 2, True), ("desktop", {"width": 1366, "height": 900}, 1, False)):
        ctx = b.new_context(viewport=vp, device_scale_factor=dsf, is_mobile=mob, has_touch=mob)
        for path in paths:
            pg = ctx.new_page(); errs = []
            pg.on("console", lambda m, e=errs: e.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda x, e=errs: e.append(str(x)))
            r = pg.goto(base + path, wait_until="networkidle")
            pg.wait_for_timeout(200)
            m = pg.evaluate("()=>({sw:document.documentElement.scrollWidth,iw:innerWidth,h:document.documentElement.scrollHeight})")
            slug = (path.strip("/") or "home").replace("/", "_")
            pg.screenshot(path=str(OUT / f"{name}_{slug}.png"), full_page=True)
            res.append({"view": name, "path": path or "/", "status": r.status, "overflow": m["sw"] > m["iw"], "scrollW": m["sw"], "height": m["h"], "errors": errs})
            pg.close()
    b.close()
if srv: srv.terminate()
for x in res: print(json.dumps(x))
