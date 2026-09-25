#!/usr/bin/env python3
"""Generates the area, service and blog pages plus sitemap.xml and robots.txt.

Run from the repo root:  python3 tools/build.py

SITE_URL must be the real production domain. Canonical tags, Open Graph URLs
and the sitemap are all absolute, and pointing them at the wrong host is worse
than omitting them. Override it without editing this file:

    SITE_URL=https://yourdomain.com python3 tools/build.py
"""
import os, sys, html, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from content_areas import AREAS
from content_services import SERVICES
from content_blog import POSTS
from content_core import CORE

SITE  = os.environ.get("SITE_URL", "https://curbsidehaulco.com").rstrip("/")
BRAND = "Curbside Haul Co."
PHONE_DISPLAY, PHONE_LINK = "(321) 364-4254", "+13213644254"
STREET, CITY, REGION, ZIP = "8305 Narcoossee Rd", "Orlando", "FL", "32827"
TODAY = datetime.date.today().isoformat()

E = lambda t: html.escape(str(t), quote=True)

LOGO = ('<svg class="logo-mark" viewBox="0 0 34 34" aria-hidden="true">'
 '<rect x="1" y="9" width="21" height="15" rx="2" fill="#1D4A37"/>'
 '<path d="M22 13h6l5 6v5H22z" fill="#EE6A1F"/>'
 '<circle cx="8" cy="27" r="4" fill="#14201A"/><circle cx="26" cy="27" r="4" fill="#14201A"/>'
 '<path d="M4 9l4-6 5 4 4-5 3 7" stroke="#C8A26A" stroke-width="2.5" fill="none" stroke-linejoin="round"/></svg>')

def nav():
    return f"""<header class="nav" id="nav">
  <div class="wrap">
    <a class="logo" href="/" aria-label="{E(BRAND)} home">{LOGO}{E(BRAND)}</a>
    <ul>
      <li><a href="/services">Services</a></li>
      <li><a href="/areas">Areas</a></li>
      <li><a href="/pricing">Pricing</a></li>
      <li><a href="/blog">Guides</a></li>
      <li><a href="/contact">Contact</a></li>
    </ul>
    <a class="phone" href="tel:{PHONE_LINK}">{PHONE_DISPLAY}</a>
    <a class="btn btn-go" href="/#quote">Get a free quote</a>
  </div>
</header>"""

def footer():
    svc = "".join(f'<li><a href="/services/{s["slug"]}">{E(s["name"])}</a></li>' for s in SERVICES[:6])
    ars = "".join(f'<li><a href="/areas/{a["slug"]}">{E(a["name"])}</a></li>' for a in AREAS)
    return f"""<footer>
  <div class="wrap">
    <div class="cols">
      <div>
        <h4>{E(BRAND)}</h4>
        <address class="nap">{E(BRAND)}<br>{STREET}<br>{CITY}, {REGION} {ZIP}<br><a href="tel:{PHONE_LINK}">{PHONE_DISPLAY}</a><br>Mon to Sat, 7am to 7pm</address>
      </div>
      <div><h4>Services</h4><ul>{svc}<li><a href="/services">All services</a></li></ul></div>
      <div><h4>Areas</h4><ul>{ars}</ul></div>
      <div><h4>Company</h4><ul><li><a href="/about">About</a></li><li><a href="/pricing">Pricing</a></li><li><a href="/same-day-junk-removal">Same-day service</a></li><li><a href="/contact">Contact</a></li><li><a href="/blog">Guides</a></li></ul></div>
    </div>
    <div class="legal">&copy; 2026 {E(BRAND)}. Licensed and insured. Business license #000000.</div>
  </div>
</footer>"""

def crumbs(trail):
    """trail: [(label, href|None)] - last item is the current page."""
    parts, items = [], []
    for i, (label, href) in enumerate(trail, 1):
        parts.append(f'<a href="{href}">{E(label)}</a>' if href else f'<span aria-current="page">{E(label)}</span>')
        items.append('{"@type":"ListItem","position":%d,"name":%s%s}' % (
            i, jstr(label), f',"item":"{SITE}{href}"' if href else ""))
    nav_html = '<nav class="crumbs" aria-label="Breadcrumb"><div class="wrap">' + '<span class="sep">/</span>'.join(parts) + '</div></nav>'
    ld = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[%s]}</script>' % ",".join(items)
    return nav_html, ld

def jstr(s):
    """JSON string literal, safe to sit inside a <script> block."""
    import json
    return json.dumps(str(s), ensure_ascii=False).replace("</", "<\\/")

def faq_block(faqs, heading="Frequently asked questions", intro=None):
    rows = "".join(
        f"<details><summary>{E(q)}</summary><p>{a}</p></details>" for q, a in faqs)
    sub = f"<p>{E(intro)}</p>" if intro else ""
    return f"""<section class="faq-sec"><div class="wrap">
  <div class="sec-head"><h2>{E(heading)}</h2>{sub}</div>
  <div class="faq">{rows}</div>
</div></section>"""

def faq_ld(faqs):
    ents = ",".join(
        '{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
        % (jstr(q), jstr(html.unescape(a.replace("<strong>","").replace("</strong>","")))) for q, a in faqs)
    return '<script type="application/ld+json">{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[%s]}</script>' % ents

def cta():
    return f"""<section class="cta-band"><div class="wrap">
  <h2>Get a price before anything moves</h2>
  <p>Send photos, get a real number, and nothing goes in the truck until you say yes.</p>
  <div class="cta-row">
    <a class="btn btn-go" href="/#quote">Get a free quote</a>
    <a class="btn btn-line" href="tel:{PHONE_LINK}">Call {PHONE_DISPLAY}</a>
  </div>
</div></section>"""

def fit_title(core, limit=60):
    """Append the brand only when the result still fits a SERP title."""
    core = core.strip()
    withbrand = f"{core} | {BRAND}"
    if len(withbrand) <= limit:
        return withbrand
    return core if len(core) <= limit else core[:limit - 1].rsplit(" ", 1)[0]

def fit_desc(text, limit=155):
    """Trim to a whole sentence under the limit, falling back to a word boundary."""
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for end in (". ", "? ", "! "):
        i = cut.rfind(end)
        if i > limit * 0.55:
            return cut[:i + 1].strip()
    return cut.rsplit(" ", 1)[0].rstrip(",;:") + "."

def page(*, path, title, desc, body, extra_ld="", og_type="website"):
    url = f"{SITE}/{path}".rstrip("/") if path else SITE
    out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{E(BRAND)}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/img/job-1.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{E(title)}">
<meta name="twitter:description" content="{E(desc)}">
<meta name="twitter:image" content="{SITE}/img/job-1.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
{extra_ld}
</head>
<body>
{nav()}
{body}
{footer()}
</body>
</html>
"""
    f = ROOT / path / "index.html" if path else ROOT / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(out, encoding="utf-8")
    return "/" + path if path else "/"

# ---------------------------------------------------------------- area pages

def build_area(a):
    by_slug = {x["slug"]: x for x in AREAS}
    nearby = "".join(
        f'<a href="/areas/{s}">{E(by_slug[s]["name"])} <span>{E(by_slug[s]["drive"])}</span></a>'
        for s in a["nearby"] if s in by_slug)
    hoods = "".join(f"<li>{E(h)}</li>" for h in a["hoods"])
    angle = "".join(
        f'<div class="take-card"><h3>{E(t)}</h3><p>{E(d)}</p></div>' for t, d in a["angle"])
    svc = "".join(
        f'<a class="chip" href="/services/{s["slug"]}">{E(s["name"])}</a>' for s in SERVICES)
    intro = "".join(f"<p>{E(p)}</p>" for p in a["intro"])
    title = fit_title(f'Junk Removal in {a["name"]}, FL')
    cn, cld = crumbs([("Home", "/"), ("Service areas", "/areas"), (a["name"], None)])

    svc_ld = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"Service",'
      '"serviceType":"Junk removal","name":%s,"areaServed":{"@type":"City","name":%s,"addressRegion":"FL"},'
      '"provider":{"@type":"LocalBusiness","name":%s,"telephone":"+1-321-364-4254",'
      '"address":{"@type":"PostalAddress","streetAddress":"%s","addressLocality":"%s","addressRegion":"%s","postalCode":"%s","addressCountry":"US"}}}</script>'
      % (jstr(f'Junk Removal in {a["name"]}, FL'), jstr(a["name"]), jstr(BRAND), STREET, CITY, REGION, ZIP))

    body = f"""{cn}
<main>
<section class="page-hero"><div class="wrap">
  <h1>Junk Removal in {E(a["name"])}, FL</h1>
  <p class="lede">{E(a["blurb"])}</p>
  <p class="meta-line"><strong>{E(a["drive"])}</strong> from our base &middot; ZIP codes {E(a["zips"])} &middot; No trip fee</p>
  <div class="cta-row">
    <a class="btn btn-go" href="/#quote">Get a free quote</a>
    <a class="btn btn-line" href="tel:{PHONE_LINK}">Call {PHONE_DISPLAY}</a>
  </div>
</div></section>

<section class="prose-sec"><div class="wrap prose">{intro}</div></section>

<section class="take"><div class="wrap">
  <div class="sec-head"><h2>{E(a["angle_h"])}</h2></div>
  <div class="take-grid">{angle}</div>
</div></section>

<section class="prose-sec"><div class="wrap prose">
  <h2>Neighborhoods we cover in {E(a["name"])}</h2>
  <ul class="hood-list">{hoods}</ul>
  <h2>Every service, available in {E(a["name"])}</h2>
  <div class="chip-row">{svc}</div>
</div></section>

{faq_block(a["faqs"], f'{a["name"]} junk removal questions')}

<section class="areas-sec"><div class="wrap">
  <div class="sec-head"><h2>Nearby areas we serve</h2></div>
  <div class="area-list">{nearby}</div>
</div></section>
{cta()}
</main>"""
    return page(path=f'areas/{a["slug"]}', title=title,
        desc=fit_desc(f'{a["blurb"]} {a["drive"]} from our base. Free quotes, no trip fee.'),
        body=body, extra_ld=cld + svc_ld + faq_ld(a["faqs"]))

# ------------------------------------------------------------- service pages

def build_service(s):
    by_slug = {x["slug"]: x for x in SERVICES}
    rel = "".join(
        f'<a class="chip" href="/services/{r}">{E(by_slug[r]["name"])}</a>' for r in s["related"] if r in by_slug)
    takes = "".join(f"<li>{E(t)}</li>" for t in s["takes"])
    areas = "".join(f'<a class="chip" href="/areas/{a["slug"]}">{E(a["name"])}</a>' for a in AREAS)
    intro = "".join(f"<p>{E(p)}</p>" for p in s["intro"])
    title = fit_title(s["h1"])
    cn, cld = crumbs([("Home", "/"), ("Services", "/services"), (s["name"], None)])

    svc_ld = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"Service",'
      '"serviceType":%s,"name":%s,"areaServed":[%s],'
      '"provider":{"@type":"LocalBusiness","name":%s,"telephone":"+1-321-364-4254",'
      '"address":{"@type":"PostalAddress","streetAddress":"%s","addressLocality":"%s","addressRegion":"%s","postalCode":"%s","addressCountry":"US"}}}</script>'
      % (jstr(s["name"]), jstr(s["h1"]),
         ",".join('{"@type":"City","name":%s,"addressRegion":"FL"}' % jstr(a["name"]) for a in AREAS),
         jstr(BRAND), STREET, CITY, REGION, ZIP))

    body = f"""{cn}
<main>
<section class="page-hero"><div class="wrap">
  <h1>{E(s["h1"])}</h1>
  <p class="lede">{E(s["blurb"])}</p>
  <div class="cta-row">
    <a class="btn btn-go" href="/#quote">Get a free quote</a>
    <a class="btn btn-line" href="tel:{PHONE_LINK}">Call {PHONE_DISPLAY}</a>
  </div>
</div></section>

<section class="prose-sec"><div class="wrap prose">{intro}
  <h2>What we take</h2>
  <ul class="take-list">{takes}</ul>
</div></section>

{faq_block(s["faqs"], f'{s["name"]} questions')}

<section class="prose-sec"><div class="wrap prose">
  <h2>Where we do it</h2>
  <div class="chip-row">{areas}</div>
  <h2>Related services</h2>
  <div class="chip-row">{rel}</div>
</div></section>
{cta()}
</main>"""
    return page(path=f'services/{s["slug"]}', title=title, desc=fit_desc(s["blurb"]),
        body=body, extra_ld=cld + svc_ld + faq_ld(s["faqs"]))

# ----------------------------------------------------------------- blog posts

def build_post(p):
    by_slug = {x["slug"]: x for x in POSTS}
    secs = []
    for sec in p["sections"]:
        h2, p1, p2, items = (list(sec) + [None, None, None, None])[:4]
        blk = f"<h2>{E(h2)}</h2>"
        if p1: blk += f"<p>{E(p1)}</p>"
        if p2: blk += f"<p>{E(p2)}</p>"
        if items: blk += "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"
        secs.append(blk)
    toc = "".join(f'<li><a href="#s{i}">{E(sec[0])}</a></li>' for i, sec in enumerate(p["sections"], 1))
    body_secs = "".join(s.replace("<h2>", f'<h2 id="s{i}">', 1) for i, s in enumerate(secs, 1))
    intro = "".join(f"<p>{E(x)}</p>" for x in p["intro"])
    rel = "".join(
        f'<a class="post-card" href="/blog/{r}"><span class="post-date">{E(by_slug[r]["date"])}</span>'
        f'<strong>{E(by_slug[r]["title"])}</strong></a>' for r in p["related"] if r in by_slug)
    cn, cld = crumbs([("Home", "/"), ("Guides", "/blog"), (p["title"], None)])
    nice = datetime.date.fromisoformat(p["date"]).strftime("%B %-d, %Y")

    art_ld = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"Article",'
      '"headline":%s,"description":%s,"datePublished":"%s","dateModified":"%s",'
      '"author":{"@type":"Organization","name":%s},'
      '"publisher":{"@type":"Organization","name":%s},'
      '"mainEntityOfPage":{"@type":"WebPage","@id":"%s/blog/%s"}}</script>'
      % (jstr(p["title"]), jstr(p["desc"]), p["date"], p["date"], jstr(BRAND), jstr(BRAND), SITE, p["slug"]))

    body = f"""{cn}
<main>
<article>
<section class="page-hero"><div class="wrap">
  <p class="meta-line"><time datetime="{p["date"]}">{nice}</time> &middot; {E(p["read"])} read</p>
  <h1>{E(p["title"])}</h1>
  <p class="lede">{E(p["desc"])}</p>
</div></section>

<section class="prose-sec"><div class="wrap prose">
  {intro}
  <nav class="toc" aria-label="On this page"><h2>On this page</h2><ol>{toc}</ol></nav>
  {body_secs}
  <div class="takeaway"><h2>The short version</h2><p>{E(p["takeaway"])}</p></div>
</div></section>
</article>

<section class="prose-sec"><div class="wrap prose">
  <h2>Related guides</h2>
  <div class="post-grid">{rel}</div>
</div></section>
{cta()}
</main>"""
    return page(path=f'blog/{p["slug"]}', title=fit_title(p.get("mt", p["title"])),
        desc=fit_desc(p["desc"]), body=body, extra_ld=cld + art_ld, og_type="article")

# ---------------------------------------------------------------- index pages

def build_indexes():
    urls = []

    cards = "".join(
      f'<a class="post-card" href="/areas/{a["slug"]}"><strong>{E(a["name"])}</strong>'
      f'<span class="post-date">{E(a["drive"])} &middot; {E(a["zips"])}</span>'
      f'<span class="card-desc">{E(a["blurb"])}</span></a>' for a in AREAS)
    cn, cld = crumbs([("Home", "/"), ("Service areas", None)])
    urls.append(page(path="areas", title=fit_title("Junk Removal Service Areas Near Orlando, FL"),
      desc=fit_desc("Lake Nona, Narcoossee, Conway, Belle Isle, St. Cloud and Kissimmee. What we haul in each and what it costs."),
      extra_ld=cld,
      body=f"""{cn}
<main>
<section class="page-hero"><div class="wrap">
  <h1>Where we work</h1>
  <p class="lede">We run out of {STREET} in {CITY}. These are the areas we cover without a trip fee, with what the work looks like in each.</p>
</div></section>
<section class="prose-sec"><div class="wrap"><div class="post-grid">{cards}</div></div></section>
{cta()}
</main>"""))

    cards = "".join(
      f'<a class="post-card" href="/services/{s["slug"]}"><strong>{E(s["name"])}</strong>'
      f'<span class="card-desc">{E(s["blurb"])}</span></a>' for s in SERVICES)
    cn, cld = crumbs([("Home", "/"), ("Services", None)])
    urls.append(page(path="services", title=fit_title("Junk Removal Services in Orlando, FL"),
      desc=fit_desc("Furniture, appliances, mattresses, garage and estate cleanouts, hot tubs, sheds and construction debris. Quoted before we load."),
      extra_ld=cld,
      body=f"""{cn}
<main>
<section class="page-hero"><div class="wrap">
  <h1>What we haul</h1>
  <p class="lede">If two people can lift it and it is not hazardous, it goes in the truck. Every service is priced the same way: by how much of the truck it fills, quoted before anything moves.</p>
</div></section>
<section class="prose-sec"><div class="wrap"><div class="post-grid">{cards}</div></div></section>
{cta()}
</main>"""))

    posts = sorted(POSTS, key=lambda x: x["date"], reverse=True)
    cards = "".join(
      f'<a class="post-card" href="/blog/{p["slug"]}">'
      f'<span class="post-date">{datetime.date.fromisoformat(p["date"]).strftime("%B %-d, %Y")} &middot; {E(p["read"])}</span>'
      f'<strong>{E(p["title"])}</strong><span class="card-desc">{E(p["desc"])}</span></a>' for p in posts)
    cn, cld = crumbs([("Home", "/"), ("Guides", None)])
    urls.append(page(path="blog", title=fit_title("Junk Removal Guides for Central Florida"),
      desc=fit_desc("Straight answers on junk removal costs, what haulers cannot take, storm debris and estate cleanouts near Orlando."),
      extra_ld=cld,
      body=f"""{cn}
<main>
<section class="page-hero"><div class="wrap">
  <h1>Guides</h1>
  <p class="lede">What we tell people who call and ask. No filler, no padding, and we will tell you when the cheapest answer is not hiring us.</p>
</div></section>
<section class="prose-sec"><div class="wrap"><div class="post-grid">{cards}</div></div></section>
{cta()}
</main>"""))
    return urls

# --------------------------------------------------------- sitemap and robots

def build_sitemap(entries):
    rows = "".join(
      f"  <url><loc>{SITE}{u}</loc><lastmod>{m}</lastmod>"
      f"<changefreq>{c}</changefreq><priority>{p}</priority></url>\n"
      for u, m, c, p in entries)
    (ROOT / "sitemap.xml").write_text(
      '<?xml version="1.0" encoding="UTF-8"?>\n'
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + "</urlset>\n",
      encoding="utf-8")
    ai = ["Google-Extended","GPTBot","OAI-SearchBot","ChatGPT-User","PerplexityBot",
          "Perplexity-User","ClaudeBot","Claude-Web","Claude-SearchBot","Applebot-Extended",
          "Amazonbot","cohere-ai","meta-externalagent"]
    social = ["Twitterbot","facebookexternalhit","LinkedInBot","WhatsApp","Slackbot"]
    blocks = [f"User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api/"]
    blocks.append("# Search engines")
    blocks += [f"User-agent: {b}\nAllow: /" for b in ["Googlebot","Googlebot-Image","Bingbot","Applebot","DuckDuckBot"]]
    blocks.append("# Answer engines. We want to be cited in AI answers, so these are allowed.")
    blocks += [f"User-agent: {b}\nAllow: /" for b in ai]
    blocks.append("# Social preview crawlers")
    blocks += [f"User-agent: {b}\nAllow: /" for b in social]
    (ROOT / "robots.txt").write_text(
      "\n\n".join(blocks) + f"\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")

# ----------------------------------------------------------------- core pages

def build_core(c):
    secs = "".join(
        f'<h2 id="s{i}">{E(h2)}</h2>' + "".join(blocks)
        for i, (h2, blocks) in enumerate(c["sections"], 1))
    svc = "".join(f'<a class="chip" href="/services/{x["slug"]}">{E(x["name"])}</a>' for x in SERVICES[:10])
    ars = "".join(f'<a class="chip" href="/areas/{x["slug"]}">{E(x["name"])}</a>' for x in AREAS)
    cn, cld = crumbs([("Home", "/"), (c["name"], None)])
    body = f"""{cn}
<main>
<section class="page-hero"><div class="wrap">
  <h1>{E(c["h1"])}</h1>
  <p class="lede">{E(c["blurb"])}</p>
  <div class="cta-row">
    <a class="btn btn-go" href="/#quote">Get a free quote</a>
    <a class="btn btn-line" href="tel:{PHONE_LINK}">Call {PHONE_DISPLAY}</a>
  </div>
</div></section>

<section class="prose-sec"><div class="wrap prose">{secs}</div></section>

{faq_block(c["faqs"], f'{c["name"]} questions')}

<section class="prose-sec"><div class="wrap prose">
  <h2>Services</h2><div class="chip-row">{svc}<a class="chip" href="/services">All services</a></div>
  <h2>Areas we cover</h2><div class="chip-row">{ars}</div>
</div></section>
{cta()}
</main>"""
    return page(path=c["slug"], title=fit_title(c.get("mt", c["h1"])),
        desc=fit_desc(c["blurb"]), body=body, extra_ld=cld + faq_ld(c["faqs"]))

def main():
    if "yourdomain" in SITE or SITE.endswith("curbsidehaulco.com"):
        print(f"!! SITE_URL is {SITE} - confirm this is the real production domain.", file=sys.stderr)
    entries = [("/", TODAY, "weekly", "1.0")]
    for u in build_indexes():
        entries.append((u, TODAY, "weekly", "0.8"))
    for c in CORE:
        entries.append((build_core(c), TODAY, "monthly", "0.9"))
    for a in AREAS:
        entries.append((build_area(a), TODAY, "monthly", "0.9"))
    for s in SERVICES:
        entries.append((build_service(s), TODAY, "monthly", "0.9"))
    for p in POSTS:
        entries.append((build_post(p), p["date"], "yearly", "0.6"))
    build_sitemap(entries)
    print(f"built {len(entries)} URLs")
    print(f"  {len(AREAS)} areas, {len(SERVICES)} services, {len(POSTS)} posts, {len(CORE)} core, 3 indexes")
    total = sum(len(x['faqs']) for x in AREAS) + sum(len(x['faqs']) for x in SERVICES) + sum(len(x['faqs']) for x in CORE)
    print(f"  {total} FAQs in schema")

if __name__ == "__main__":
    main()
