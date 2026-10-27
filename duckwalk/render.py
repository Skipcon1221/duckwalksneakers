"""HTML rendering (stdlib only, no template engine needed)."""
import json
from html import escape as e

from .links import listing_url, store_search_url, store_home_url
from .models import size_sort_key


def fmt_price(v, cur="USD"):
    return ("$" if cur == "USD" else cur + " ") + (f"{v:,.0f}" if v == int(v) else f"{v:,.2f}")


def size_label(s):
    return f"US {s}" if s else "Size n/a"


def size_range(sizes):
    sizes = sorted({s for s in sizes if s}, key=size_sort_key)
    if not sizes:
        return ""
    return sizes[0] if len(sizes) == 1 else f"{sizes[0]}\u2013{sizes[-1]}"


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def layout(ctx, *, title, description, canonical_path, body, head_extra="", og_image=""):
    cfg = ctx["cfg"]
    base = cfg["base_url"].rstrip("/")
    sample_banner = ""
    if ctx["sample"]:
        sample_banner = ('<div class="sample-banner">SAMPLE DATA PREVIEW: these are invented listings, '
                         'prices and photos for layout only. Live eBay listings replace them automatically.</div>')
    epn_on = bool((cfg.get("epn_campaign_id") or "").strip())
    # EPN Network Agreement: disclosure must be clear and prominent, so it sits at the top of every page.
    epn_top = ('<p class="epn-disclosure">Ad disclosure: links to eBay on this site are affiliate links. '
               'As an eBay Partner Network Affiliate, we earn from qualifying purchases.</p>') if epn_on else ""
    epn_note = " Links to eBay are eBay Partner Network affiliate links, and we earn from qualifying purchases." if epn_on else ""
    og = f'<meta property="og:image" content="{e(og_image if og_image.startswith("http") else base + og_image)}">' if og_image else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(base + canonical_path)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(cfg['site_name'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(base + canonical_path)}">
{og}
<meta name="twitter:card" content="summary_large_image">
{'<meta name="robots" content="noindex">' if ctx["sample"] else ''}
<link rel="stylesheet" href="/assets/style.css?v={ctx['build_id']}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
{head_extra}
</head>
<body>
{sample_banner}
<header class="site-header"><div class="wrap">
  <a class="logo" href="/"><span class="logo-mark" aria-hidden="true">&#x1F986;</span>{e(cfg['site_name'])}</a>
  <nav><a href="/#brands">Brands</a><a class="btn btn-small" href="{e(store_home_url(cfg, ctx['seller']))}" rel="noopener">Full store on eBay</a></nav>
</div></header>
<main class="wrap">
{epn_top}
{updated_line(ctx)}
{body}
</main>
<footer class="site-footer"><div class="wrap">
  <p><strong>{e(cfg['site_name'])}</strong> &middot; Naples, Florida. All items are listed and sold on eBay; checkout, payment, shipping and returns are handled on eBay.
  {e(cfg['site_name'])} is an independent eBay seller. This site is not run, endorsed or sponsored by eBay.{epn_note}</p>
  <p class="muted">Listing photos, prices and sizes come from our own live eBay listings and refresh every few hours. Always confirm the final price, shipping and details on eBay before buying.
  Brand and model names are trademarks of their owners and are used only to describe the items; we are not affiliated with any sneaker brand.</p>
  <p class="footer-links"><a href="/privacy/">Privacy</a> &middot; <a href="https://www.ebay.com/help/policies/member-behavior-policies/user-agreement?id=4259" rel="noopener">eBay User Agreement</a> &middot; <a href="https://www.ebay.com/help/policies/member-behavior-policies/user-privacy-notice-privacy-policy?id=4260" rel="noopener">eBay Privacy Notice</a></p>
</div></footer>
<script>
(function(){{var el=document.querySelector('[data-built]');if(!el)return;
var t=new Date(el.getAttribute('data-built')).getTime(),h=(Date.now()-t)/36e5,max={ctx['max_age']};
var s=h<1?'less than an hour ago':(Math.floor(h)===1?'1 hour ago':Math.floor(h)+' hours ago');
if(h>=24)s=Math.floor(h/24)+(Math.floor(h/24)===1?' day ago':' days ago');
el.querySelector('.ago').textContent=s;
if(h>max){{document.body.classList.add('stale');}}}})();
</script>
</body>
</html>
"""


def updated_line(ctx):
    return (f'<p class="updated" data-built="{e(ctx["built_iso"])}">Listings updated '
            f'<span class="ago">{e(ctx["built_human"])}</span>'
            f'<span class="stale-note">. This data may be out of date. Prices and sizes may have changed; please confirm on eBay.</span></p>')


def ship_label(l):
    s = l.get("shipping", "")
    if s == "free":
        return "Free shipping"
    if s:
        return f"+ ${s} shipping"
    return "Shipping: see eBay"


def ebay_block(inner, note="From our live eBay listings"):
    """API License 8.1(b)(2): eBay Content is shown in its own, labeled box, kept apart from our own copy."""
    return f'<section class="ebay-block"><p class="ebay-block-label">{e(note)}</p>{inner}</section>'


def card(m, ctx):
    instock = m["in_stock"]
    if instock:
        sizes = size_range([l["size"] for l in m["listings"]])
        low = min(l["price"] for l in m["listings"])
        meta = f'<span>US {e(sizes)}</span><span class="price">from {e(fmt_price(low))}</span>'
        badge = ""
    else:
        meta = '<span class="muted">Sold out for now</span>'
        badge = '<span class="badge">Sold out</span>'
    img = m.get("image") or ("/assets/no-photo.svg" if instock else "/assets/sold-out.svg")
    return f"""<a class="card{' card-out' if not instock else ''}" href="/{e(m['slug'])}/">
  <div class="card-img">{badge}<img src="{e(img)}" alt="{e(m['name'])}" loading="lazy" width="300" height="300"></div>
  <div class="card-body"><h3>{e(m['name'])}</h3><div class="card-meta">{meta}</div></div>
</a>"""


def placeholder(ctx, label, hint):
    if not ctx["preview"]:
        return ""
    return f'<div class="placeholder"><strong>PLACEHOLDER: {e(label)}</strong><br>{e(hint)}</div>'


def content_section(ctx, content, key, heading, hint):
    text = (content or {}).get(key, "").strip()
    if text:
        paras = "".join(f"<p>{e(p.strip())}</p>" for p in text.split("\n\n") if p.strip())
        return f'<section class="prose"><h2>{e(heading)}</h2>{paras}</section>'
    return placeholder(ctx, heading, hint)


def model_page(m, ctx, similar, content):
    cfg, seller = ctx["cfg"], ctx["seller"]
    base = cfg["base_url"].rstrip("/")
    path = f"/{m['slug']}/"
    search = store_search_url(m["search_query"], cfg, seller)
    sizes = [l["size"] for l in m["listings"]]
    srange = size_range(sizes)
    sc = f" {m['style_code']}" if m.get("style_code") else ""
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": cfg["site_name"], "item": base + "/"},
        {"@type": "ListItem", "position": 2, "name": m["brand"], "item": f"{base}/brand/{m['brand_slug']}/"},
        {"@type": "ListItem", "position": 3, "name": m["name"], "item": base + path}]}
    ld = [crumbs]

    if m["in_stock"]:
        prices = [l["price"] for l in m["listings"]]
        title = f"{m['name']}{sc} \u2013 US Sizes {srange} | {cfg['site_name']}"
        conds = sorted({l["condition"] for l in m["listings"] if l["condition"]})
        size_list = ", ".join(sorted({s for s in sizes if s}, key=size_sort_key))
        desc = (f"Shop the {m['name']}{(' (' + m['style_code'] + ')') if m.get('style_code') else ''} in US sizes {size_list}"
                f" from {fmt_price(min(prices))}. {', '.join(conds)}. Sold on eBay by {cfg['site_name']}.")
        imgs = [l["image"] for l in m["listings"] if l["image"]]
        prod = {"@context": "https://schema.org", "@type": "Product", "name": m["name"],
                "image": [i if i.startswith("http") else base + i for i in dict.fromkeys(imgs)][:6],
                "description": desc, "brand": {"@type": "Brand", "name": m["brand"]},
                "offers": {"@type": "AggregateOffer", "priceCurrency": m["listings"][0]["currency"],
                           "lowPrice": f"{min(prices):.2f}", "highPrice": f"{max(prices):.2f}",
                           "offerCount": len(prices), "availability": "https://schema.org/InStock", "url": base + path}}
        if m.get("style_code"):
            prod["sku"] = prod["mpn"] = m["style_code"]
        if m.get("colorway"):
            prod["color"] = m["colorway"]
        ld.append(prod)

        rows = []
        for l in m["listings"]:
            rows.append(f"""<li class="size-row">
  <img src="{e(l['image'] or '/assets/no-photo.svg')}" alt="{e(m['name'])} {e(size_label(l['size']))}" loading="lazy" width="96" height="96">
  <div class="size-info"><div class="size">{e(size_label(l['size']))}</div><div class="cond">{e(l['condition'])}</div></div>
  <div class="size-price">{'<span class="bid">Current bid</span>' if l.get('auction') else ''}{e(fmt_price(l['price'], l['currency']))}<div class="ship">{e(ship_label(l))}</div></div>
  <a class="btn" href="{e(listing_url(l, cfg))}" rel="{'sponsored ' if cfg.get('epn_campaign_id') else ''}noopener">Buy on eBay</a>
</li>""")
        stock_html = f"""<section class="stock"><h2>Sizes in stock ({len(m['listings'])})</h2>
<ul class="size-list">{''.join(rows)}</ul>
<p class="store-link">Don't see your size? <a href="{e(search)}" rel="noopener">See every {e(m['name'])} pair in our eBay store &rarr;</a></p></section>"""
        hero_img = m["image"]
        status = f'<p class="status in">In stock &middot; US {e(srange)} &middot; from {e(fmt_price(min(prices)))}</p>'
    else:
        title = f"{m['name']}{sc} \u2013 Sold Out | {cfg['site_name']}"
        desc = (f"The {m['name']}{(' (' + m['style_code'] + ')') if m.get('style_code') else ''} is sold out at "
                f"{cfg['site_name']} right now. Check our eBay store for new pairs or shop similar sneakers in stock.")
        stock_html = f"""<section class="soldout-box"><h2>Sold out for now</h2>
<p>We don't have the {e(m['name'])} listed right now. New pairs come in often, so
<a href="{e(search)}" rel="noopener">check our eBay store for this model</a>, or shop similar pairs below.</p></section>"""
        hero_img = ""  # the listing is gone, so its eBay photo is not shown or kept
        status = '<p class="status out">Sold out</p>'

    details = ""
    if m["in_stock"]:  # item specifics are eBay Content: shown only while the listing is live
        facts = [("Brand", m.get("brand")), ("Model", m.get("model")), ("Colorway", m.get("colorway")),
                 ("Style code", m.get("style_code")), ("Release year", m.get("release_year")),
                 ("Conditions available", ", ".join(sorted({l["condition"] for l in m["listings"] if l["condition"]})))]
        facts_html = "".join(f"<tr><th>{e(k)}</th><td>{e(v)}</td></tr>" for k, v in facts if v)
        details = f'<section class="facts"><h2>Details</h2><table>{facts_html}</table><p class="muted small">From our eBay listing item specifics.</p></section>' if facts_html else ""

    content_html = (
        content_section(ctx, content, "about", f"About the {m['name']}", "Short, factual intro to this model/colorway. Only add facts you can verify (e.g. from Nike/brand release notes). Edit data/*/model_content.json.")
        + content_section(ctx, content, "release_info", "Release info", "Verified release date, retail price and release notes. Leave empty rather than guess.")
        + content_section(ctx, content, "fit_notes", "Fit & sizing", "How this model fits (true to size / half size up), from Mark's experience or the brand's guidance.")
    )

    similar_html = ""
    if similar:
        similar_html = f'<section class="similar"><h2>{"Similar pairs in stock" if not m["in_stock"] else "You might also like"}</h2><div class="grid">{"".join(card(s, ctx) for s in similar)}</div></section>'

    head = f"""<div class="model-head"><p class="brand">{e(m['brand'])}</p><h1>{e(m['name'])}</h1>
  {f'<p class="code">Style code {e(m["style_code"])}</p>' if m.get('style_code') else ''}
  {status}
  <a class="btn btn-ghost" href="{e(search)}" rel="noopener">Search this model in our eBay store</a></div>"""
    if m["in_stock"]:
        ebay_html = ebay_block(f"""<div class="model-hero">
  <div class="model-img"><img src="{e(hero_img or '/assets/no-photo.svg')}" alt="{e(m['name'])}" width="600" height="600"></div>
  {head}
</div>
{stock_html}
{details}""")
    else:
        ebay_html = f"""<div class="model-hero">
  <div class="model-img"><img src="/assets/sold-out.svg" alt="" width="600" height="600"></div>
  {head}
</div>
{stock_html}"""
    own_html = f'<div class="own-content"><p class="own-label">From {e(cfg["site_name"])}</p>{content_html}</div>' if content_html else ""
    if similar:
        similar_html = ebay_block(f'<h2>{"Similar pairs in stock" if not m["in_stock"] else "You might also like"}</h2><div class="grid">{"".join(card(s, ctx) for s in similar)}</div>',
                                  "Similar pairs from our live eBay listings")

    body = f"""<nav class="crumbs"><a href="/">Home</a> / <a href="/brand/{e(m['brand_slug'])}/">{e(m['brand'])}</a> / <span>{e(m['name'])}</span></nav>
<article class="model{' is-out' if not m['in_stock'] else ''}">
{ebay_html}
{own_html}
</article>
{similar_html}"""
    return layout(ctx, title=title, description=desc, canonical_path=path, body=body,
                  head_extra="".join(jsonld(x) for x in ld), og_image=hero_img or "")


def home_page(ctx, brands):
    cfg = ctx["cfg"]
    base = cfg["base_url"].rstrip("/")
    total_pairs = sum(len(m["listings"]) for ms in brands.values() for m in ms if m["in_stock"])
    total_models = sum(1 for ms in brands.values() for m in ms if m["in_stock"])
    chips = "".join(f'<a class="chip" href="/brand/{e(b_slug)}/">{e(name)}</a>' for (name, b_slug) in ctx["brand_index"])
    sections = []
    for (bname, b_slug) in ctx["brand_index"]:
        ms = brands[bname]
        sections.append(f'<section class="brand-sec" id="b-{e(b_slug)}"><div class="sec-head"><h2>{e(bname)}</h2>'
                        f'<a href="/brand/{e(b_slug)}/">All {e(bname)} &rarr;</a></div>'
                        + ebay_block(f'<div class="grid">{"".join(card(m, ctx) for m in ms)}</div>') + '</section>')
    body = f"""<section class="hero">
  <h1>{e(cfg['site_name'])}</h1>
  <p class="lead">{e(cfg['tagline'])}</p>
  <p class="hero-stats"><strong>{total_pairs}</strong> pairs across <strong>{total_models}</strong> models in stock now</p>
  <div class="hero-cta"><a class="btn" href="{e(store_home_url(cfg, ctx['seller']))}" rel="noopener">Shop the full store on eBay</a></div>
</section>
<section id="brands"><h2 class="visually-hidden">Brands</h2><div class="chips">{chips}</div></section>
{''.join(sections)}"""
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": cfg["site_name"], "url": base + "/"}
    return layout(ctx, title=f"{cfg['site_name']} \u2013 Jordan, Nike, adidas & more sneakers by size",
                  description=f"{cfg['site_name']}: shop {total_pairs} sneakers in stock by model and size, including "
                              + ", ".join(b for b, _ in ctx["brand_index"][:4]) + ". Every pair is sold on eBay.",
                  canonical_path="/", body=body, head_extra=jsonld(ld))


def brand_page(ctx, bname, b_slug, models):
    cfg = ctx["cfg"]
    n_in = sum(1 for m in models if m["in_stock"])
    body = f"""<nav class="crumbs"><a href="/">Home</a> / <span>{e(bname)}</span></nav>
<section class="brand-sec"><h1>{e(bname)} sneakers</h1><p class="lead">{n_in} {e(bname)} models in stock now. Pick a model to see every size and price.</p>
{ebay_block('<div class="grid">' + ''.join(card(m, ctx) for m in models) + '</div>')}</section>"""
    return layout(ctx, title=f"{bname} Sneakers by Model & Size | {cfg['site_name']}",
                  description=f"Shop {n_in} {bname} sneaker models in stock at {cfg['site_name']}, with every size and price. Sold on eBay.",
                  canonical_path=f"/brand/{b_slug}/", body=body)


def not_found_page(ctx):
    # Old Shopify URLs (/products/..., /collections/...) land here; send people home.
    body = """<section class="hero"><h1>That page moved</h1><p class="lead">Our old shop pages are gone. Taking you to the current sneaker list&hellip;</p>
<p><a class="btn" href="/">Go to the home page</a></p></section>
<script>if(/^\\/(products|collections|pages|cart|shop)/.test(location.pathname)){setTimeout(function(){location.replace('/')},1200);}</script>"""
    return layout(ctx, title=f"Page not found | {ctx['cfg']['site_name']}", description="Page not found.",
                  canonical_path="/404.html", body=body, head_extra='<meta name="robots" content="noindex">')


def privacy_page(ctx):
    cfg = ctx["cfg"]
    epn = bool((cfg.get("epn_campaign_id") or "").strip())
    n = e(cfg["site_name"])
    body = f"""<section class="prose privacy"><h1>Privacy policy</h1>
<p>{n} is a simple catalog of the sneakers we have listed for sale on eBay. This page explains what happens to your information when you visit.</p>
<h2>What we collect</h2>
<p>Nothing. This site has no accounts, no forms, no checkout, no analytics and no cookies of its own. We do not ask for, receive or store any personal information.</p>
<h2>Hosting</h2>
<p>The site is hosted on GitHub Pages. Like any web host, GitHub may log technical data such as your IP address when you load a page, for security and to run the service. See the
<a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener">GitHub Privacy Statement</a>.</p>
<h2>Photos and eBay links</h2>
<p>Listing photos load directly from eBay's image servers. When you click a link to eBay, you leave this site and eBay's own
<a href="https://www.ebay.com/help/policies/member-behavior-policies/user-privacy-notice-privacy-policy?id=4260" rel="noopener">privacy notice</a> applies.
{'Links to eBay are eBay Partner Network affiliate links, so eBay may use cookies to credit us for qualifying purchases.' if epn else ''}</p>
<h2>eBay data</h2>
<p>Listing details on this site come from our own eBay listings through eBay's public API. We do not collect or keep any data about eBay buyers or other eBay users.</p>
<h2>Contact</h2>
<p>Questions about this policy can be sent through our eBay store's contact option.</p>
</section>"""
    return layout(ctx, title=f"Privacy policy | {cfg['site_name']}", description=f"Privacy policy for {cfg['site_name']}.",
                  canonical_path="/privacy/", body=body)
