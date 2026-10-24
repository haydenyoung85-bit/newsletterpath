#!/usr/bin/env python3
"""Builds the static site into docs/ from data/*.json.  Run: python3 scripts/build_site.py"""
import json, pathlib, html, shutil
R = pathlib.Path(__file__).resolve().parent.parent
S = R / "docs"
P = json.load(open(R / "data/platforms.json"))
G = json.load(open(R / "data/programs.json"))
CFG = json.load(open(R / "data/config.json"))
CH = json.load(open(R / "data/changes.json"))["entries"]
BASE = CFG["base"]; PRE = CFG["path_prefix"]
U = P["last_verified"]
PL = {p["id"]: p for p in P["platforms"]}
PR = G["programs"]
E = html.escape

def cta(x): return x.get("affiliate_url") or x["url"]
def rel(x): return "sponsored noopener" if x.get("affiliate_url") else "noopener"
def money(v):
    if v is None: return "–"
    return "$" + (("%.2f" % v).rstrip("0").rstrip(".") if v % 1 else "%d" % v)
def fnum(n): return f"{n:,}"
FREE_SHORT = {"beehiiv":"2,500 subs","kit":"10,000 subs","substack":"Unlimited","ghost":"Trial only","mailerlite":"250 subs",
              "buttondown":"100 subs","mailchimp":"250 contacts","flodesk":"No sending","aweber":"Trial only",
              "emailoctopus":"2,500 subs","getresponse":"Trial only"}
def minshort(p):
    h, s = p["min_hard"], p["min_soft"]
    if h is None: t = "Not published"
    elif h == 0: t = "None published"
    else: t = fnum(h)
    if s: t += f" (suggested {fnum(s)}+)" if p["id"] == "sparkloop" else f" (built for {fnum(s)}+)"
    return t
def links(urls): return " ".join(f'<a href="{E(u)}" rel="noopener" target="_blank">[{i+1}]</a>' for i, u in enumerate(urls))

SECTIONS = []  # (path, lastmod)
NAV = [("", "Compare"), ("platform-fees/", "Fees"), ("ad-networks/", "Ad networks"), ("changes/", "Changes"), ("methodology/", "Method")]
FORM = CFG.get("kit_form_id")
def capture():
    if not FORM: return ""
    return f'''<section class="cap"><b>Get the weekly changes</b><span>Price or program changes, once a week.</span>
<form id="nl" method="post" action="https://app.kit.com/forms/{FORM}/subscriptions"><input type="email" name="email_address" required placeholder="you@email.com" aria-label="Email address" autocomplete="email"><button>Subscribe</button></form><i id="nlmsg" class="sm"></i></section>'''
GC = f'<script data-goatcounter="{CFG["goatcounter"]}/count" async src="//gc.zgo.at/count.js"></script>' if CFG.get("goatcounter") else ""

def page(path, title, desc, body, schema=None, js=False, h1_mod=None):
    url = f"{BASE}/{path}"
    up = PRE + "/"
    nav = "".join(f'<a href="{up}{h}"{" class=on" if h == path else ""}>{t}</a>' for h, t in NAV)
    sc = schema or [{"@context": "https://schema.org", "@type": "WebPage", "name": title, "description": desc, "dateModified": U, "url": url}]
    out = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{url}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{url}">
<meta name="theme-color" content="#0b5d4b"><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E%3Crect width=%2732%27 height=%2732%27 rx=%277%27 fill=%27%230b5d4b%27/%3E%3Cpath d=%27M8 24 L14 12 L19 19 L24 8%27 stroke=%27%23f4b942%27 stroke-width=%273.5%27 fill=%27none%27 stroke-linecap=%27round%27/%3E%3C/svg%3E">
<link rel="stylesheet" href="{up}assets/style.css"><script type="application/ld+json">{json.dumps(sc)}</script></head><body>
<header><div class="wrap hd"><a class="logo" href="{up}">Newsletter<b>Path</b></a><nav>{nav}</nav></div></header><main class="wrap">{body}</main>
<footer><div class="wrap">Checked {U} against each vendor's public pages. Some outbound links may become affiliate links; that never changes a ranking. <a href="{up}methodology/#affiliate-disclosure">Disclosure</a> · <a href="{up}changes/">Changes</a> · <a href="{up}sitemap.xml">Sitemap</a></div></footer>
{f'<script src="{up}assets/data.js"></script><script src="{up}assets/app.js" defer></script>' if js else ''}{f'<script src="{up}assets/form.js" defer></script>' if FORM else ''}{GC}
</body></html>'''
    f = S / path / "index.html" if path else S / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True); f.write_text(out)
    SECTIONS.append(path); return path

def faq(qs): return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qs]}
def wp(title, desc, path, extra=None):
    d = {"@context": "https://schema.org", "@type": "WebPage", "name": title, "description": desc, "dateModified": U, "url": f"{BASE}/{path}"}
    return [d] + ([extra] if extra else [])

# ---------------------------------------------------------------- data.js for JS features
JSD = {"platforms": [{k: p.get(k) for k in ("id","name","m1","y1","m5","y5","charge_plan","charge_m1","charge_y1","charge_m5","charge_y5","fee_pct","charge_unconfirmed")} for p in P["platforms"]],
       "programs": [{"id": p["id"], "hard": p["min_hard"], "soft": p["min_soft"]} for p in PR]}
(S / "assets").mkdir(parents=True, exist_ok=True)
(S / "assets/data.js").write_text("window.NP=" + json.dumps(JSD, separators=(",", ":")) + ";")

# ---------------------------------------------------------------- helpers: tables
def cell_price(p, n, bill="m"):
    return money(p.get(f"{bill}{n}"))
def plat_rows(order=None):
    rows = []
    for p in (order or P["platforms"]):
        fee = p["fee_text"]
        feeshort = "n/p" if p["fee_pct"] is None else f"{p['fee_pct']:g}% + proc."
        if p["id"] == "kit": feeshort = "3.5% + $0.30"
        rows.append(f'''<tr data-id="{p["id"]}" data-name="{E(p["name"])}" data-free="{p.get("free_limit") or 0}" data-freeall="{1 if p["id"]=="substack" else 0}" data-m1="{p["m1"]}" data-y1="{p["y1"] if p["y1"] is not None else ""}" data-m5="{p["m5"]}" data-y5="{p["y5"] if p["y5"] is not None else ""}" data-fee="{p["fee_pct"] if p["fee_pct"] is not None else ""}">
<th scope="row" data-l="Platform"><a href="{E(cta(p))}" rel="{rel(p)}" target="_blank">{E(p["name"])}</a><small>{E(p["plan1"])}{"" if p["plan1"]==p["plan5"] else " → "+E(p["plan5"])}</small></th>
<td data-l="Free tier" class="fr">{FREE_SHORT[p["id"]]}<em class="ok" hidden>covers you</em></td>
<td data-l="At 1,000" class="p" data-n="1">{cell_price(p,1)}</td><td data-l="At 5,000" class="p" data-n="5">{cell_price(p,5)}</td>
<td data-l="Fee on paid subs" class="fe" title="{E(fee)}">{E(feeshort)}</td></tr>''')
    return "".join(rows)

# ---------------------------------------------------------------- HOME
proglist = sorted(PR, key=lambda x: (x["min_hard"] is None, x["min_hard"] or 0, x["name"]))
home_progs = "".join(f'<li data-hard="{"" if p["min_hard"] is None else p["min_hard"]}"><a href="{PRE}/ad-networks/#{p["id"]}">{E(p["name"])}</a><span>{E(minshort(p))}</span><em></em></li>' for p in proglist)
body = f'''<h1>Newsletter platform prices &amp; sponsor minimums</h1>
<p class="lead">{len(PL)} platforms and {len(PR)} monetization programs. Every figure is read from the vendor's own page; if it isn't published, it says so.</p>
<div class="ctl"><label>My list size<select id="size"><option value="100">100</option><option value="500">500</option><option value="1000" selected>1,000</option><option value="2500">2,500</option><option value="5000">5,000</option><option value="10000">10,000</option><option value="25000">25,000</option><option value="50000">50,000</option></select></label>
<label>Sort<select id="sort"><option value="name">Name</option><option value="p1" selected>Price @1k</option><option value="p5">Price @5k</option><option value="free">Biggest free tier</option><option value="fee">Lowest paid-sub fee</option></select></label>
<label>Billing<select id="bill"><option value="m">Monthly</option><option value="y">Yearly (per month)</option></select></label></div>
<div class="tw"><table id="pt" class="cards"><thead><tr><th data-k="name">Platform</th><th data-k="free">Free tier</th><th data-k="p1">@1,000</th><th data-k="p5">@5,000</th><th data-k="fee">Fee on paid subs</th></tr></thead><tbody>{plat_rows()}</tbody></table></div>
<p class="sm" id="note">Price = cheapest plan that covers that list size, USD per month, before tax. “n/p” = not published; “proc.” = card processing on top. <a href="{PRE}/platform-fees/">Plans, notes and sources</a> · <a href="{PRE}/cheapest-platform-to-charge-for-a-newsletter/">Cheapest to charge readers</a></p>
<h2>What takes a list your size?</h2>
<ul id="pl" class="pl">{home_progs}</ul>
<p class="sm"><a href="{PRE}/ad-networks/">Shares, payout terms and sources for every program</a> · <a href="{PRE}/newsletter-ad-network-minimum-subscribers/">Minimums explained</a></p>
{capture()}'''
page("", "Newsletter Platform Prices & Sponsor Minimums (2026) | NewsletterPath",
     "Compare beehiiv, Kit, Substack, Ghost, MailerLite and more: price at 1k and 5k subscribers, free tiers, fees on paid subscriptions, and ad network minimums. Sourced and dated.", body, js=True)

# ---------------------------------------------------------------- PLATFORM FEES
det = ""
for p in P["platforms"]:
    det += f'''<details id="{p["id"]}"><summary><b>{E(p["name"])}</b> <span class="sm">{E(p["plan1"])} {money(p["m1"])} @1k · {E(p["plan5"])} {money(p["m5"])} @5k</span></summary>
<ul class="sm"><li><b>Free tier:</b> {E(p["free_note"])}</li><li><b>Yearly billing, per month:</b> {money(p["y1"])} @1k · {money(p["y5"])} @5k</li>
<li><b>Fee on paid subscriptions:</b> {E(p["fee_text"])}{f' (<a href="{E(p["fee_src"])}" rel="noopener" target="_blank">source</a>)' if p.get("fee_src") else ""}</li>
{f'<li>{E(p["extras"])}</li>' if p["extras"] else ""}<li><b>Sources:</b> {links(p["sources"])} · verified {p["last_verified"]}</li></ul></details>'''
srt = sorted([p for p in P["platforms"] if p["fee_pct"] is not None], key=lambda p: (p["fee_pct"], p["name"]))
frows = "".join(f'<tr><th scope="row" data-l="Platform">{E(p["name"])}</th><td data-l="Platform fee">{p["fee_pct"]:g}%</td><td data-l="Detail">{E(p["fee_text"])}</td><td data-l="Source"><a href="{E(p["fee_src"])}" rel="noopener" target="_blank">page</a></td></tr>' for p in srt)
na = ", ".join(p["name"] for p in P["platforms"] if p["fee_pct"] is None)
body = f'''<h1>Platform fees for newsletters under 5,000 subscribers</h1>
<p class="lead">Monthly price at 1,000 and 5,000 subscribers, free-tier limits, and what each platform takes when you charge readers.</p>
<h2>Fee on paid subscriptions</h2><div class="tw"><table class="cards"><thead><tr><th>Platform</th><th>Fee</th><th>Detail</th><th>Source</th></tr></thead><tbody>{frows}</tbody></table></div>
<p class="sm">Not published / not offered on the pages checked: {E(na)}. Card processing (Stripe is typically 2.9% + $0.30) comes on top unless the row says it is included.</p>
<h2>Per-platform detail</h2><div class="acc">{det}</div>
<p class="sm">Prices change often; see <a href="{PRE}/changes/">the change log</a> and <a href="{PRE}/methodology/">how we verify</a>.</p>{capture()}'''
page("platform-fees/", "Newsletter Platform Fees at 1k & 5k Subscribers | NewsletterPath",
     "Monthly price at 1,000 and 5,000 subscribers for beehiiv, Kit, Substack, Ghost, MailerLite, Buttondown and more, plus free-tier limits and fees on paid subscriptions.", body)

# ---------------------------------------------------------------- AD NETWORKS
def prow(p):
    return f'''<tr id="{p["id"]}" data-hard="{"" if p["min_hard"] is None else p["min_hard"]}"><th scope="row" data-l="Program"><a href="{E(p["signup"])}" rel="noopener" target="_blank">{E(p["name"])}</a><small>{E(p["kind"])}</small></th>
<td data-l="Minimum subscribers">{E(p["min_text"])}</td><td data-l="Revenue share / fees">{E(p["share"])}</td><td data-l="Payout terms">{E(p["payout"])}</td>
<td data-l="Sources">{links(p["sources"])}<small>verified {p["last_verified"]}</small></td></tr>'''
notes = "".join(f'<li><b>{E(p["name"])}:</b> {E(p["note"])}</li>' for p in PR if p.get("note"))
body = f'''<h1>Newsletter ad networks and sponsorship programs</h1>
<p class="lead">Minimum subscribers, revenue share and payout terms, from each program's own pages. “Not published” means we found nothing official to quote.</p>
<div class="ctl"><label>My list size<select id="size"><option value="">Any</option><option value="500">500</option><option value="1000">1,000</option><option value="5000">5,000</option><option value="10000">10,000</option><option value="25000">25,000</option><option value="50000">50,000</option></select></label></div>
<div class="tw"><table id="at" class="cards"><thead><tr><th>Program</th><th>Minimum subs</th><th>Share / fees</th><th>Payout</th><th>Sources</th></tr></thead><tbody>{"".join(prow(p) for p in proglist)}</tbody></table></div>
<ul class="sm">{notes}</ul>
<p class="sm">Related: <a href="{PRE}/newsletter-ad-network-minimum-subscribers/">minimums by program</a> · <a href="{PRE}/how-many-subscribers-for-newsletter-sponsorships/">how many subscribers for sponsorships</a>.</p>{capture()}'''
page("ad-networks/", "Newsletter Ad Networks: Minimums & Payouts | NewsletterPath",
     "beehiiv Ad Network, Kit, SparkLoop, Paved, Passionfroot, Swapstack, Letterhead, EmailNewsletter.ad and Sponsy: minimum subscribers, fees and payouts.", body, js=True)

# ---------------------------------------------------------------- CHANGES
if CH:
    rows = "".join(f'<tr><td data-l="Date">{E(c["date"])}</td><td data-l="Item">{E(c["item"])}</td><td data-l="Field">{E(c["field"])}</td><td data-l="Was">{E(str(c["old"]))}</td><td data-l="Now">{E(str(c["new"]))}</td></tr>' for c in reversed(CH))
    ch = f'<div class="tw"><table class="cards"><thead><tr><th>Date</th><th>Item</th><th>Field</th><th>Was</th><th>Now</th></tr></thead><tbody>{rows}</tbody></table></div>'
else:
    ch = '<div class="card">No changes logged yet. Baseline recorded <b>' + U + '</b>. The weekly check compares each source page to this baseline and lists differences here.</div>'
body = f'''<h1>Price and program changes</h1><p class="lead">A running log of what changed on vendor pages since the baseline of {U}.</p>{ch}
<p class="sm">The check runs <code>scripts/update_check.py</code>; entries are added only when a published number or phrase on a source page differs from the saved baseline.</p>{capture()}'''
page("changes/", "Newsletter Platform Price Changes Log | NewsletterPath", "Weekly log of price, free-tier and ad-network term changes across newsletter platforms. Baseline " + U + ".", body)

# ---------------------------------------------------------------- METHODOLOGY
body = f'''<div class="prose"><h1>Methodology and disclosure</h1>
<h2>What counts as verified</h2><p>A number is shown only if we read it on the vendor's own pricing, help-center or terms page (or rendered the pricing slider to read it). Each row carries its source links and the date we checked it ({U}). If a figure is missing, we write “not published” or leave it blank. We do not estimate.</p>
<h2>How prices are chosen</h2><ul><li>“At 1,000 / 5,000” is the cheapest plan that covers that list size, in USD per month, monthly billing unless you switch to yearly.</li><li>Yearly means the yearly price divided by 12.</li><li>Some sliders skip sizes. Buttondown has no 5,000 step, so we show the 4,800 tier. Ghost Starter stops at 1,000 members, so the 5,000 figure is Publisher.</li><li>Flodesk 5,000 and annual prices come from the rendered price list on its page, while the 1,000 monthly prices were confirmed on screen.</li></ul>
<h2>Programs</h2><p>Minimum subscribers, revenue share and payout terms come from each program's help center, pricing page or terms. Rates paid by advertisers vary by campaign and are not promised anywhere here.</p>
<h2>Known gaps</h2><ul><li>Kit sponsorships, Swapstack, Passionfroot and Letterhead do not publish payout schedules we could quote.</li><li>Paid-subscription fees for Mailchimp and EmailOctopus are not published, because we found no paid-newsletter feature on their pricing pages.</li><li>Which plan unlocks paid newsletters on Kit and GetResponse is flagged as unconfirmed.</li></ul>
<h2 id="affiliate-disclosure">Affiliate disclosure</h2><p>NewsletterPath may earn a commission if you sign up through some outbound links, at no cost to you. Today the links go to the vendors' plain official pages and no affiliate links are active. If that changes, those links will carry <code>rel="sponsored"</code>, and this section will say which vendors. Commissions never change a figure, sort order or recommendation on the site.</p>
<h2>Corrections</h2><p>Found something out of date? Check the vendor page linked on the row; the weekly check also logs changes on the <a href="{PRE}/changes/">changes page</a>.</p></div>{capture()}'''
page("methodology/", "Methodology, Sources & Affiliate Disclosure | NewsletterPath", "How NewsletterPath verifies prices and program terms, what is left blank, and how affiliate links are disclosed.", body)

# ---------------------------------------------------------------- LONG-TAIL 1: minimum subscribers
L1 = [("Does the beehiiv Ad Network have a minimum subscriber count?", "No minimum is published. It is available on any paid plan to publishers actively sending on beehiiv."),
      ("What is Paved's minimum?", "At least 50,000 subscribers for the Paved Ad Network."),
      ("What is the minimum for EmailNewsletter.ad?", "You can apply at any size, but it is built primarily for 25,000+ subscribers and every newsletter is reviewed."),
      ("Does SparkLoop require a minimum?", "No defined minimum; SparkLoop suggests waiting until you have 500 to 1,000 subscribers.")]
def minrows(ids): return "".join(f'<tr><th scope="row" data-l="Program"><a href="{PRE}/ad-networks/#{p["id"]}">{E(p["name"])}</a></th><td data-l="Minimum">{E(p["min_text"])}</td><td data-l="Needs">{E(p["requires"])}</td></tr>' for p in PR if p["id"] in ids)
body = f'''<h1>Newsletter ad network minimum subscribers</h1>
<p class="lead"><b>Short answer:</b> most programs publish no hard minimum. The two hard numbers we found are 50,000 (Paved Ad Network) and a 25,000+ target (EmailNewsletter.ad). SparkLoop suggests 500 to 1,000.</p>
<h2>Minimums by program</h2><div class="tw"><table class="cards"><thead><tr><th>Program</th><th>Minimum subscribers</th><th>Needs</th></tr></thead><tbody>{minrows([p["id"] for p in proglist])}</tbody></table></div>
<h2>Read this before you rely on “no minimum”</h2><ul><li>“Not published” is not “no limit”. Marketplaces such as Passionfroot vet profiles; audience size is one input, B2B fit matters more.</li><li>beehiiv and Kit tie their programs to paid plans, so the real cost of entry is the plan price (see <a href="{PRE}/platform-fees/">fees</a>).</li><li>Click- and subscriber-based programs pay little until your list is engaged and sized well past these floors. The pages we checked publish no earnings estimates, so we give none.</li></ul>
<h2>FAQ</h2>{"".join(f"<h3>{E(q)}</h3><p>{E(a)}</p>" for q,a in L1)}
<p class="sm">Full terms and sources: <a href="{PRE}/ad-networks/">ad networks table</a>.</p>{capture()}'''
page("newsletter-ad-network-minimum-subscribers/", "Newsletter Ad Network Minimum Subscribers (2026) | NewsletterPath",
     "What list size do newsletter ad networks require? beehiiv, Kit, SparkLoop, Paved (50,000), EmailNewsletter.ad (25,000+ target) and others, with sources.", body, faq(L1) and wp("Newsletter ad network minimum subscribers", "Minimums by program", "newsletter-ad-network-minimum-subscribers/", faq(L1)))

# ---------------------------------------------------------------- LONG-TAIL 2: how many subscribers for sponsorships
def band(lo, hi):
    names = [p for p in proglist if p["min_hard"] is not None and p["min_hard"] <= lo]
    return ", ".join(p["name"] for p in names)
unk = ", ".join(p["name"] for p in proglist if p["min_hard"] is None)
L2 = [("How many subscribers do I need for newsletter sponsorships?", "There is no single official number. Of the programs checked, only Paved's Ad Network (50,000) and EmailNewsletter.ad (25,000+ target) publish a floor. beehiiv, Kit, SparkLoop and Passionfroot publish no hard minimum."),
      ("Can I get sponsors with under 1,000 subscribers?", "Programs such as the beehiiv Ad Network, Kit sponsorships and the SparkLoop Partner Network publish no hard minimum, though beehiiv and Kit require a paid plan and SparkLoop suggests 500 to 1,000 subscribers first.")]
body = f'''<h1>How many subscribers do you need for newsletter sponsorships?</h1>
<p class="lead"><b>Short answer:</b> there is no official industry threshold. Programs publish either no minimum or a floor of 25,000 to 50,000. Here is what is open at each list size, using only published terms.</p>
<h2>Open at each list size</h2><div class="tw"><table class="cards"><thead><tr><th>List size</th><th>Programs with no higher published floor</th></tr></thead><tbody>
<tr><th scope="row" data-l="List size">Under 1,000</th><td data-l="Programs">{E(band(0,0))}</td></tr>
<tr><th scope="row" data-l="List size">1,000 to 24,999</th><td data-l="Programs">{E(band(1000,0))} (same programs; SparkLoop's suggested 500+ is met)</td></tr>
<tr><th scope="row" data-l="List size">25,000 to 49,999</th><td data-l="Programs">{E(band(25000,0))}; EmailNewsletter.ad reaches its target size</td></tr>
<tr><th scope="row" data-l="List size">50,000+</th><td data-l="Programs">{E(band(50000,0))}, including Paved Ad Network</td></tr></tbody></table></div>
<p class="sm">Not published, so we cannot place them: {E(unk)}.</p>
<h2>What the programs actually say</h2><ul>
<li><b>beehiiv Ad Network:</b> paid plan and active sending; CPM or CPC set per campaign.</li>
<li><b>Kit sponsorships:</b> paid plan; pays per unique verified click; no minimum stated.</li>
<li><b>SparkLoop:</b> no defined minimum, suggests 500 to 1,000; brands pay $2 to $20 per new subscriber per SparkLoop's page.</li>
<li><b>Passionfroot:</b> no minimum published; profiles are vetted with a B2B focus, and a “Limited” profile stays off the marketplace but can still receive direct requests.</li>
<li><b>Paved Ad Network:</b> 50,000 subscribers.</li></ul>
<h2>FAQ</h2>{"".join(f"<h3>{E(q)}</h3><p>{E(a)}</p>" for q,a in L2)}
<p class="sm">Sources and payout terms: <a href="{PRE}/ad-networks/">ad networks table</a>.</p>{capture()}'''
page("how-many-subscribers-for-newsletter-sponsorships/", "Subscribers Needed for Newsletter Sponsorships | NewsletterPath",
     "No official threshold exists. See which ad networks and sponsorship programs are open at under 1,000, 25,000 and 50,000+ subscribers, from their own published terms.", body, wp("How many subscribers for newsletter sponsorships", "Open programs by list size", "how-many-subscribers-for-newsletter-sponsorships/", faq(L2)))

# ---------------------------------------------------------------- LONG-TAIL 3: Kit vs beehiiv
b, k = PL["beehiiv"], PL["kit"]
bi, ki = next(p for p in PR if p["id"] == "beehiiv-ad-network"), next(p for p in PR if p["id"] == "kit-sponsorships")
L3 = [("Is Kit or beehiiv cheaper under 1,000 subscribers?", "Both have free plans (Kit up to 10,000 subscribers, beehiiv up to 2,500), so both cost $0 under 1,000 subscribers. Paid plans at 1,000 subscribers: beehiiv Lite $59/mo, Kit Creator $39/mo, both on monthly billing."),
      ("Can I use the beehiiv Ad Network on the free plan?", "No. beehiiv's pricing page shows no Ad Network or paid subscriptions on Free; Lite and up include them."),
      ("Which charges less on paid newsletter subscriptions?", "beehiiv takes 0% plus Stripe's fee. Kit takes 3.5% + $0.30 including card processing, which its pricing page describes as Kit keeping 0.6%.")]
body = f'''<h1>Kit vs beehiiv for a newsletter under 1,000 subscribers</h1>
<p class="lead"><b>Short answer:</b> both are free at this size. The question is when you pay to unlock monetization: beehiiv needs a paid plan for its Ad Network and paid subscriptions, and so does Kit for sponsorships.</p>
<div class="tw"><table class="cards"><thead><tr><th>Under 1,000 subscribers</th><th>beehiiv</th><th>Kit</th></tr></thead><tbody>
<tr><th scope="row" data-l="Item">Free plan limit</th><td data-l="beehiiv">{E(b["free_note"])}</td><td data-l="Kit">{E(k["free_note"])}</td></tr>
<tr><th scope="row" data-l="Item">Cheapest paid plan at 1,000</th><td data-l="beehiiv">Lite {money(b["m1"])}/mo monthly, {money(b["y1"])}/mo yearly</td><td data-l="Kit">Creator {money(k["m1"])}/mo monthly, {money(k["y1"])}/mo yearly</td></tr>
<tr><th scope="row" data-l="Item">At 5,000</th><td data-l="beehiiv">Lite {money(b["m5"])}/mo monthly, {money(b["y5"])} yearly</td><td data-l="Kit">Creator {money(k["m5"])}/mo monthly, {money(k["y5"])} yearly</td></tr>
<tr><th scope="row" data-l="Item">Fee on paid subscriptions</th><td data-l="beehiiv">{E(b["fee_text"])}</td><td data-l="Kit">{E(k["fee_text"])}</td></tr>
<tr><th scope="row" data-l="Item">Sponsorships</th><td data-l="beehiiv">Ad Network: {E(bi["min_text"])}</td><td data-l="Kit">{E(ki["min_text"])}</td></tr>
<tr><th scope="row" data-l="Item">Paid recommendations</th><td data-l="beehiiv">Included in Lite per its pricing page</td><td data-l="Kit">Via Creator Network and SparkLoop; Kit keeps 23.5%</td></tr>
</tbody></table></div>
<h2>How to choose</h2><ul><li><b>Just starting, no revenue yet:</b> stay on either free plan. Neither can run sponsorship ads on Free.</li><li><b>Want the cheapest paid step:</b> Kit Creator at {money(k["m1"])}/mo vs beehiiv Lite at {money(b["m1"])}/mo (monthly billing).</li><li><b>Plan to charge readers:</b> beehiiv keeps 0% of subscription revenue; Kit keeps 0.6%. At small revenue the difference is cents.</li></ul>
<h2>FAQ</h2>{"".join(f"<h3>{E(q)}</h3><p>{E(a)}</p>" for q,a in L3)}
<p class="sm">Sources: {links(b["sources"]+k["sources"])} · checked {U}. Not verified: whether Kit's Free plan includes paid newsletters.</p>
<p class="cta"><a class="btn" href="{E(cta(b))}" rel="{rel(b)}" target="_blank">beehiiv</a> <a class="btn" href="{E(cta(k))}" rel="{rel(k)}" target="_blank">Kit</a></p>{capture()}'''
page("kit-vs-beehiiv-under-1000-subscribers/", "Kit vs beehiiv Under 1,000 Subscribers (2026) | NewsletterPath",
     "Kit vs beehiiv for a small newsletter: free plan limits, price at 1,000 and 5,000 subscribers, fees on paid subscriptions and sponsorship requirements, with sources.", body, wp("Kit vs beehiiv under 1,000 subscribers", "Comparison", "kit-vs-beehiiv-under-1000-subscribers/", faq(L3)))

# ---------------------------------------------------------------- LONG-TAIL 4: cheapest to charge
ch_rows = []
for p in P["platforms"]:
    if p.get("charge_plan") is None or p["id"] == "flodesk": continue
    m1 = p.get("charge_m1", p["m1"]); m5 = p.get("charge_m5", p["m5"])
    if p["id"] == "ghost": m5 = p["m5"]
    ch_rows.append((p, m1, m5))
sub = PL["substack"]
def be(p, m):
    d = 10 - p["fee_pct"]
    return None if d <= 0 else m / (d / 100)
ch_rows.sort(key=lambda r: (r[1] + 0.0, r[0]["name"]))
trs = ""
for p, m1, m5 in ch_rows:
    flag = " *" if p.get("charge_unconfirmed") else ""
    b1 = "" if p["id"] == "substack" else (money(round(be(p, m1))) if be(p, m1) else "–")
    trs += f'<tr><th scope="row" data-l="Platform">{E(p["name"])}<small>{E(p["charge_plan"])}{flag}</small></th><td data-l="@1k /mo">{money(m1)}</td><td data-l="@5k /mo">{money(m5)}</td><td data-l="Fee on sales">{p["fee_pct"]:g}%</td><td data-l="Beats Substack above">{b1 and (b1+"/mo revenue")}</td></tr>'
L4 = [("What is the cheapest platform to charge for a newsletter?", "Substack has no monthly fee but keeps 10% of subscription revenue. Among flat-price platforms, Buttondown's Basic plan ($9/mo at 1,000 subscribers) takes 0% and includes paid subscriptions, followed by MailerLite Comfort ($19/mo). Card processing applies everywhere."),
      ("When does Substack's 10% cost more than a flat-fee platform?", "When your monthly subscription revenue passes the plan price divided by 10%. For Buttondown at $9 that is about $90/mo; for beehiiv Lite at $59 it is about $590/mo.")]
body = f'''<h1>Cheapest platform to charge for a newsletter</h1>
<p class="lead"><b>Short answer:</b> for a small paid list, Substack is cheapest until about $90 a month in revenue, Buttondown ($9/mo at 1,000 subscribers) is the cheapest flat-fee plan, with MailerLite Comfort ($19/mo) next. These figures exclude card processing, which every platform passes on.</p>
<div class="calc card"><b>Your monthly cost</b><div class="ctl"><label>List size<select id="cl"><option value="1">1,000</option><option value="5">5,000</option></select></label><label>Paying readers<input id="cn" type="number" min="0" value="50" inputmode="numeric"></label><label>Price $/mo<input id="cp" type="number" min="0" step="0.5" value="6" inputmode="decimal"></label></div>
<ol id="cr" class="rank"></ol><span class="sm">Platform plan + platform fee on revenue. Excludes Stripe processing (2.9% + $0.30 typical), which Kit includes in its 3.5% + $0.30.</span></div>
<h2>Ranked by plan price at 1,000 subscribers</h2><div class="tw"><table class="cards"><thead><tr><th>Platform</th><th>@1k /mo</th><th>@5k /mo</th><th>Fee</th><th>Beats Substack above</th></tr></thead><tbody>{trs}</tbody></table></div>
<p class="sm">Cheapest plan on each platform that supports charging readers; monthly billing. * Plan unconfirmed on the vendor page. Ghost @5k is Publisher because Starter stops at 1,000 members. Mailchimp and EmailOctopus show no paid-newsletter feature, and Flodesk Checkout is a product checkout rather than a gated newsletter, so all three are left out.</p>
<h2>FAQ</h2>{"".join(f"<h3>{E(q)}</h3><p>{E(a)}</p>" for q,a in L4)}
<p class="sm">Sources: <a href="{PRE}/platform-fees/">platform fees</a> · checked {U}.</p>{capture()}'''
page("cheapest-platform-to-charge-for-a-newsletter/", "Cheapest Platform to Charge for a Newsletter (2026) | NewsletterPath",
     "Compare plan prices and fees for charging newsletter subscribers on Substack, Buttondown, MailerLite, Ghost, Kit, beehiiv, AWeber and more, with a cost calculator.", body, wp("Cheapest platform to charge for a newsletter", "Ranking and calculator", "cheapest-platform-to-charge-for-a-newsletter/", faq(L4)), js=True)

# ---------------------------------------------------------------- 404, sitemap, robots, data
(S / "404.html").write_text(f'<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Not found | NewsletterPath</title><link rel="stylesheet" href="{PRE}/assets/style.css"><main class="wrap"><h1>Page not found</h1><p><a href="{PRE}/">Back to the comparison</a></p></main>')
(S / "data").mkdir(exist_ok=True)
for n in ("platforms", "programs"): shutil.copy(R / f"data/{n}.json", S / f"data/{n}.json")
(S / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{BASE}/{p}</loc><lastmod>{U}</lastmod></url>" for p in SECTIONS) + "</urlset>")
(S / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
(S / ".nojekyll").write_text("")
print(len(SECTIONS), "pages")
