#!/usr/bin/env python3
"""duckwalksneakers static site generator.

  python3 build.py              # live eBay data if EBAY_CLIENT_ID/EBAY_CLIENT_SECRET are set, else SAMPLE data
  python3 build.py --sample     # force the labeled sample fixture
  python3 build.py --preview    # also show content PLACEHOLDER boxes (never use for the public deploy)
  REQUIRE_LIVE=1 python3 build.py   # CI: fail instead of publishing sample data

Output goes to ./site/ . Pages are never deleted: every model ever seen is kept in a
registry (data/<mode>/registry.json); sold-out models keep their page with a notice.
"""
import hashlib
import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from duckwalk import ebay
from duckwalk.models import group, group_report, slugify, size_sort_key
from duckwalk import render

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "site")


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def write(rel, html):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def tokens(s):
    return set(re.findall(r"[a-z0-9]+", (s or "").lower())) - {"air", "retro", "og", "the", "nike", "jordan"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()

    cfg = load_json(os.path.join(ROOT, "config.json"), {})
    if os.environ.get("EPN_CAMPAIGN_ID"):
        cfg["epn_campaign_id"] = os.environ["EPN_CAMPAIGN_ID"]
    use_live = ebay.live_credentials_present() and not args.sample
    if os.environ.get("REQUIRE_LIVE") == "1" and not use_live:
        sys.exit("REQUIRE_LIVE=1 but EBAY_CLIENT_ID / EBAY_CLIENT_SECRET are missing; refusing to publish sample data.")

    mode = "live" if use_live else "sample"
    ddir = os.path.join(ROOT, "data", mode)
    if mode == "sample":
        ddir = os.path.join(ROOT, "data", "sample")
        items, seller = ebay.load_sample(os.path.join(ddir, "sample_listings.json"))
        reg_path = os.path.join(ddir, "registry.json")
        if not os.path.exists(reg_path):
            shutil.copy(os.path.join(ddir, "registry_seed.json"), reg_path)
    else:
        items, seller = ebay.load_live(cfg)
        reg_path = os.path.join(ddir, "registry.json")
    n_listings = len({(i.get("itemId", "").split("|") + ["", ""])[1] or i.get("itemId") for i in items})
    print(f"[{mode}] {len(items)} in-stock sizes across {n_listings} eBay listings for seller {seller}")

    tz = ZoneInfo(cfg.get("timezone", "America/New_York"))
    now = datetime.now(timezone.utc).astimezone(tz)
    now_iso = now.isoformat(timespec="seconds")

    registry = load_json(reg_path, {"models": {}})
    reg = registry.setdefault("models", {})
    content_path = os.path.join(ddir, "model_content.json")
    content = load_json(content_path, {})
    content.setdefault("_help", "Per-model page copy keyed by URL slug. Only verified facts. Empty fields are hidden on the public site.")

    current = group(items)
    print(group_report(items, current))
    used_slugs = {r["slug"]: k for k, r in reg.items()}

    # Merge live groups into the permanent registry (slugs never change once assigned).
    for key, g in current.items():
        r = reg.get(key)
        if r is None:
            slug = g["default_slug"] or slugify(key)
            if slug in used_slugs and used_slugs[slug] != key:
                slug = f"{slug}-{slugify(g['style_code'] or key)}"
            used_slugs[slug] = key
            r = reg[key] = {"slug": slug, "first_seen": now_iso, "last_changed": now_iso, "signature": ""}
        # Persist only what is needed to keep the page (name, slug, search words). Photos,
        # prices and other listing data are never written to the public repo.
        for f in ("name", "brand", "model", "colorway", "style_code", "search_query"):
            if g.get(f):
                r[f] = g[f]
        r["last_in_stock"] = now_iso
        # Only a hash is stored, so the public repo holds no listing prices or item IDs.
        sig = hashlib.sha1("|".join(f"{l['item_id']}:{l['price']}:{l['size']}" for l in g["listings"]).encode()).hexdigest()[:16]
        if sig != r.get("signature"):
            r["signature"], r["last_changed"] = sig, now_iso
    for key, r in reg.items():
        if key not in current:
            if r.get("signature"):
                r["signature"], r["last_changed"] = "", now_iso  # just sold out
    for r in reg.values():  # clean up fields older builds stored (API License 8.1(b)(1), 3.1(b))
        for f in ("image", "release_year"):
            r.pop(f, None)

    # Build model view objects for every model ever seen.
    models = []
    for key, r in reg.items():
        g = current.get(key)
        m = dict(r)
        m["key"] = key
        m["in_stock"] = bool(g)
        m["listings"] = g["listings"] if g else []
        m["brand"] = m.get("brand") or "Other"
        m["brand_slug"] = slugify(m["brand"])
        # Photo and release year come only from the live listing; sold-out pages show neither.
        m["image"] = g["image"] if g else ""
        m["release_year"] = g.get("release_year", "") if g else ""
        models.append(m)
        content.setdefault(m["slug"], {"about": "", "release_info": "", "fit_notes": ""})

    # Home/brand ordering: in-stock first (most pairs), sold-out after.
    def order(m):
        return (not m["in_stock"], -len(m["listings"]), m["name"])
    brands = {}
    for m in sorted(models, key=order):
        brands.setdefault(m["brand"], []).append(m)
    brand_index = sorted(((b, slugify(b)) for b in brands),
                         key=lambda x: (-sum(len(m["listings"]) for m in brands[x[0]]), x[0]))

    ctx = {
        "cfg": cfg, "seller": seller, "sample": mode == "sample", "preview": args.preview,
        "built_iso": now_iso, "built_human": now.strftime("%b %-d, %Y, %-I:%M %p ET"),
        "build_id": now.strftime("%Y%m%d%H%M"), "max_age": cfg.get("max_data_age_hours", 6),
        "brand_index": brand_index,
    }

    # Fresh output dir; static assets first.
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(os.path.join(ROOT, "static"), OUT,
                    ignore=None if mode == "sample" else shutil.ignore_patterns("sample-img"))

    in_stock = [m for m in models if m["in_stock"]]
    for m in models:
        mt = tokens(m["name"])
        cands = [s for s in in_stock if s["key"] != m["key"]]
        cands.sort(key=lambda s: (s["brand"] != m["brand"], -len(mt & tokens(s["name"])), -len(s["listings"])))
        write(f"{m['slug']}/index.html", render.model_page(m, ctx, cands[:4], content.get(m["slug"])))
    for bname, b_slug in brand_index:
        write(f"brand/{b_slug}/index.html", render.brand_page(ctx, bname, b_slug, brands[bname]))
    write("index.html", render.home_page(ctx, brands))
    write("404.html", render.not_found_page(ctx))
    write("privacy/index.html", render.privacy_page(ctx))

    base = cfg["base_url"].rstrip("/")
    urls = [(base + "/", now_iso), (base + "/privacy/", now_iso)]
    urls += [(f"{base}/brand/{bs}/", now_iso) for _, bs in brand_index]
    urls += [(f"{base}/{m['slug']}/", m.get("last_changed", now_iso)) for m in sorted(models, key=lambda x: x["slug"])]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{u}</loc><lastmod>{lm[:10]}</lastmod></url>" for u, lm in urls]
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")
    if mode == "sample":
        write("robots.txt", "# SAMPLE build: keep out of search engines\nUser-agent: *\nDisallow: /\n")
    else:
        write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n")
    if cfg.get("custom_domain"):
        write("CNAME", cfg["custom_domain"] + "\n")
    write(".nojekyll", "")
    write("build-info.json", json.dumps({"built": now_iso, "mode": mode, "models": len(models),
                                         "models_in_stock": len(in_stock), "listings": n_listings,
                                         "sizes_in_stock": len(items)}, indent=1))

    save_json(reg_path, registry)
    save_json(content_path, content)
    print(f"built {len(models)} model pages ({len(in_stock)} in stock, {len(models) - len(in_stock)} sold out), "
          f"{len(brand_index)} brand pages -> {OUT}")


if __name__ == "__main__":
    main()
