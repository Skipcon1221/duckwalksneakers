"""Turn raw eBay item summaries into per-MODEL groups (one page per model)."""
import re
import unicodedata

STYLE_CODE_RES = [
    re.compile(r"\b([A-Z]{2}\d{4}-\d{3})\b"),   # Nike/Jordan: FV5029-006
    re.compile(r"\b(\d{6}-\d{3})\b"),           # older Nike/Jordan: 555088-063
    re.compile(r"\b([A-Z]{1,2}\d{4,5})\b"),     # adidas: HQ6316, GW0089
]
SIZE_RE = re.compile(
    r"\b(?:size|sz|us|men'?s|mens|women'?s|womens|gs)\s*[:#]?\s*(\d{1,2}(?:\.5)?\s*[YCWy]?)\b", re.I)
NOISE_RE = re.compile(
    r"\b(size|sz|us|mens?|men's|womens?|women's|gs|new|used|ds|nib|nwb|vnds|pre-?owned|"
    r"brand|with|box|authentic|og all|100%|free ship(ping)?)\b", re.I)


def aspects(item):
    out = {}
    for a in item.get("localizedAspects", []) or []:
        name = (a.get("name") or "").strip().lower()
        if name and name not in out:
            out[name] = (a.get("value") or "").strip()
    return out


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", text)


def nice_slug(brand, model, colorway):
    m = re.sub(r"^air\s+(?=jordan)", "", model, flags=re.I)
    m = re.sub(r"\b(retro|protro)\b", "", m, flags=re.I)
    base = f"{m} {colorway}".strip()
    if brand and not base.lower().startswith(brand.lower()) and brand.lower() != "jordan":
        base = f"{brand} {base}"
    return slugify(base)


def parse_size(item, asp):
    raw = asp.get("us shoe size") or asp.get("us shoe size (men's)") or asp.get("us shoe size (women's)")
    if not raw:  # other size specifics eBay uses (youth, kids, generic "Size", sock sizes)
        for name in ("us shoe size (youth)", "us shoe size (kids)", "us shoe size (baby & toddler)",
                     "us size", "shoe size", "size"):
            if asp.get(name):
                raw = asp[name]
                break
    if not raw:
        m = SIZE_RE.search(item.get("title", ""))
        raw = m.group(1) if m else ""
    raw = raw.replace(" ", "").upper()
    return raw


def size_sort_key(size):
    m = re.match(r"(\d+(?:\.5)?)([YCW]?)", size or "")
    if not m:
        return (9, 999.0)
    suffix_rank = {"C": 0, "Y": 1, "": 2, "W": 3}[m.group(2)]
    return (suffix_rank, float(m.group(1)))


def style_code_source(item, asp):
    """(code, where it came from): 'aspect', 'title' or 'none'."""
    sc = asp.get("style code") or asp.get("manufacturer part number") or asp.get("mpn") or ""
    if sc and sc.lower() not in ("does not apply", "n/a", "na"):
        return sc.upper().strip(), "aspect"
    for rx in STYLE_CODE_RES:
        m = rx.search(item.get("title", ""))
        if m:
            return m.group(1).upper(), "title"
    return "", "none"


def parse_style_code(item, asp):
    return style_code_source(item, asp)[0]


def title_model_name(title):
    t = SIZE_RE.sub(" ", title)
    for rx in STYLE_CODE_RES:
        t = rx.sub(" ", t)
    t = NOISE_RE.sub(" ", t)
    return re.sub(r"\s{2,}", " ", t).strip(" -|,")


def normalize(item):
    asp = aspects(item)
    brand = asp.get("brand", "")
    model = asp.get("model", "")
    colorway = asp.get("colorway", "")
    style = parse_style_code(item, asp)
    if not model:
        model = title_model_name(item.get("title", ""))
        colorway = ""
    if not brand:
        low = item.get("title", "").lower()
        for b in ("Jordan", "Nike", "adidas", "New Balance", "Asics", "Puma", "Reebok", "Converse", "Vans", "Salomon", "On", "Hoka"):
            if b.lower() in low:
                brand = b
                break
        brand = brand or "Other"
    auction = "AUCTION" in (item.get("buyingOptions") or []) and "FIXED_PRICE" not in (item.get("buyingOptions") or [])
    price = (item.get("currentBidPrice") if auction else None) or item.get("price") or item.get("currentBidPrice") or {}
    ship = ""
    for so in item.get("shippingOptions") or []:
        c = so.get("shippingCost") or {}
        if c.get("value") is not None:
            ship = "free" if float(c["value"]) == 0 else f"{float(c['value']):.2f}"
            break
    img = (item.get("image") or {}).get("imageUrl") or ""
    if not img and item.get("thumbnailImages"):
        img = item["thumbnailImages"][0].get("imageUrl", "")
    return {
        "item_id": item["itemId"],
        "parent_id": (item["itemId"].split("|") + ["", ""])[1] or item["itemId"],
        "style_src": style_code_source(item, asp)[1],
        "has_aspects": bool(asp),
        "title": item.get("title", ""),
        "brand": brand,
        "model": model,
        "colorway": colorway,
        "style_code": style,
        "size": parse_size(item, asp),
        "department": asp.get("department", ""),
        "release_year": asp.get("release year", "") or asp.get("year manufactured", ""),
        "price": float(price.get("value") or 0),
        "currency": price.get("currency", "USD"),
        "condition": item.get("condition", ""),
        "image": img,
        "url": item.get("itemWebUrl", ""),
        "affiliate_url": item.get("itemAffiliateWebUrl", ""),
        "buying_options": item.get("buyingOptions", []),
        "auction": auction,
        "shipping": ship,  # "free", "12.50", or "" (unknown: shown as "see eBay")
    }


def group_key(n):
    return n["style_code"].lower() if n["style_code"] else "m-" + slugify(f'{n["brand"]} {n["model"]} {n["colorway"]}')


def display_name(brand, model, colorway):
    name = model
    if brand and brand.lower() not in model.lower() and brand.lower() != "jordan":
        name = f"{brand} {model}"
    return f"{name} \u201c{colorway}\u201d" if colorway else name


def group(items):
    groups = {}
    for it in items:
        n = normalize(it)
        groups.setdefault(group_key(n), []).append(n)
    out = {}
    for key, listings in groups.items():
        listings.sort(key=lambda x: (size_sort_key(x["size"]), x["price"]))
        first = listings[0]
        # most common values across listings for robustness
        def mode(field):
            vals = [l[field] for l in listings if l[field]]
            return max(set(vals), key=vals.count) if vals else ""
        brand, model, colorway = mode("brand"), mode("model"), mode("colorway")
        out[key] = {
            "key": key,
            "brand": brand,
            "model": model,
            "colorway": colorway,
            "style_code": mode("style_code"),
            "release_year": mode("release_year"),
            "department": mode("department"),
            "name": display_name(brand, model, colorway),
            "default_slug": nice_slug(brand, model, colorway),
            "image": next((l["image"] for l in listings if l["image"]), ""),
            "search_query": " ".join(x for x in [model if brand.lower() in model.lower() else f"{brand} {model}", colorway] if x).strip(),
            "listings": listings,
        }
    return out


def group_report(items, groups):
    """Counts only, for the build log: how listings turned into models."""
    from collections import Counter, defaultdict
    src = Counter(l["style_src"] for g in groups.values() for l in g["listings"])
    no_asp = sum(1 for g in groups.values() for l in g["listings"] if not l["has_aspects"])
    no_size = sum(1 for g in groups.values() for l in g["listings"] if not l["size"])
    parents = defaultdict(set)
    for k, g in groups.items():
        for l in g["listings"]:
            parents[l["parent_id"]].add(k)
    multi_parent = sum(1 for g in groups.values() if len({l["parent_id"] for l in g["listings"]}) > 1)
    split = sum(1 for v in parents.values() if len(v) > 1)
    keyed = Counter("style" if not k.startswith("m-") else "name" for k in groups)
    ids = Counter(l["item_id"] for g in groups.values() for l in g["listings"])
    nosize_names = Counter(n for it in items if not parse_size(it, aspects(it)) for n in aspects(it) if "size" in n)
    nostyle_brands = Counter(l["brand"] for g in groups.values() for l in g["listings"] if l["style_src"] == "none")
    return (f"  grouping: {len(items)} items -> {len(groups)} models ({keyed['style']} by style code, "
            f"{keyed['name']} by name); {len(parents)} eBay listings; models with >1 listing={multi_parent}; "
            f"listings split over >1 model={split}; style code from aspects={src['aspect']} title={src['title']} "
            f"none={src['none']}; items without aspects={no_asp}; without size={no_size}; "
            f"duplicate item ids={sum(c - 1 for c in ids.values() if c > 1)}\n"
            f"  size-like aspect names on items with no size: {dict(nosize_names)}; "
            f"brands of items with no style code: {dict(nostyle_brands)}")
