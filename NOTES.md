# NewsletterPath: notes

Live: https://haydenyoung85-bit.github.io/newsletterpath/  (GitHub Pages, branch `main`, folder `/docs`)
Repo: https://github.com/haydenyoung85-bit/newsletterpath

## How it works
Static site. `scripts/build_site.py` reads `data/platforms.json`, `data/programs.json`, `data/changes.json`, `data/config.json`
and writes everything in `docs/` (pages, `assets/data.js`, `sitemap.xml`, `robots.txt`, `404.html`). `docs/assets/style.css`,
`app.js` (sort/filter/calculator) and `form.js` (email capture) are hand-written and committed.

## Rebuild
    python3 scripts/build_site.py
    git add -A && git commit -m "update" && git push      # Pages redeploys in about a minute

## Updating data (the verification rule)
Every number must be read from the vendor's own pricing/help/terms page. If you cannot verify it, set it to `null` or write
"Not published". Never estimate. When you change a row, also set that row's `last_verified` and the file's top-level
`last_verified`. Each row keeps its `sources` URLs.
* `platforms.json`: m1/y1 (price at 1,000, monthly / yearly-per-month), m5/y5 (at 5,000), `free_limit`, `fee_pct`, `fee_text`.
* `programs.json`: `min_hard` (published floor; 0 = none published; null = not published), `min_soft` (suggested/target), `min_text`, `share`, `payout`.
* Pricing sliders (beehiiv, Kit, Buttondown, Ghost, etc.) need a real browser. Use Playwright with `/usr/bin/google-chrome --no-sandbox`
  and read the rendered text or take a screenshot (see `scripts/render.py`, `scripts/probe.py`). `scripts/grepurl.py <url> <regex>` greps a page.
* Kit.com and support.substack.com return HTTP 403 "Just a moment" to scripts. WebFetch or a normal browser can read them.

## Weekly check (not scheduled)
    python3 scripts/update_check.py --init   # once, or after you intentionally re-verify everything: saves data/baseline.json
    python3 scripts/update_check.py          # weekly: renders every source URL, compares money/percent/subscriber-count tokens to the baseline
It writes `logs/update_<date>.log`, appends differences to `data/changes.json` (shown on /changes), and never edits the price data.
A flagged change means: open the page, re-read the real number, edit the JSON, rebuild, push. BLOCKED pages are skipped.
To automate, run it from cron or a GitHub Action later; it needs Chrome + `pip install playwright`.

## Affiliate links
`affiliate_url` is `null` on every platform and program. When approved, paste the tracking URL into `affiliate_url`; the build then uses it
for the outbound button and adds `rel="sponsored"`. The disclosure lives at `/methodology/#affiliate-disclosure` and the footer links to it.
Sign-up pages: beehiiv https://www.beehiiv.com/partners (apply: https://app.beehiiv.com/partner_program),
Kit https://kit.com/affiliate (apply: https://dash.partnerstack.com/application?company=kit&group=kitaffiliates).

## Email capture
Not live yet. The build adds a Kit form block on every page as soon as `data/config.json` has `"kit_form_id": <id>`; it POSTs to
`https://app.kit.com/forms/<id>/subscriptions` with field `email_address`. A second Kit form could not be created automatically because
Kit asked for an email device-verification link on login. Create a form in Kit (Grow > Landing Pages & Forms), put its ID in config, rebuild.
The StackCost form (10085348) was deliberately NOT reused.

## Analytics
GoatCounter was skipped: its free plan is for non-commercial sites, and this site may earn affiliate commissions.
Use GitHub traffic data (14-day window, needs repo admin; `gh` is signed in):
    gh api repos/haydenyoung85-bit/newsletterpath/traffic/views
    gh api repos/haydenyoung85-bit/newsletterpath/traffic/popular/referrers
If you later set `"goatcounter": "https://<code>.goatcounter.com"` in config.json (e.g. on a paid plan) the build adds the tag.

## Testing
    python3 scripts/screenshots.py [base_url]   # phone 390x844 and desktop 1366x900 screenshots into shots/, overflow + console error report
    python3 scripts/check_links.py [base_url]   # meta tags per page, every internal/external link status, anchors
Pass the live URL to test production; with no argument it serves `docs/` locally under `/newsletterpath/`.

## Secrets
Never commit credentials. `.gitignore` excludes `.secrets*`, `*_state.json`, `.env`, `raw/` and `shots/`.
