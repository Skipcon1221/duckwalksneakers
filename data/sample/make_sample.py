"""Generates data/sample/sample_listings.json + placeholder photos.
EVERYTHING HERE IS SAMPLE DATA - not Mark's real listings or prices."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "..", "..", "static", "sample-img")
os.makedirs(IMG_DIR, exist_ok=True)

# (brand, model, colorway, style code, release year, dept, color1, color2, [(size, price, condition)])
MODELS = [
 ("Jordan","Air Jordan 4 Retro","Bred Reimagined","FV5029-006","2024","Men","#1b1b1b","#c8102e",
  [("9","245.00","New with box"),("10.5","260.00","New with box"),("13","285.00","New with box")]),
 ("Jordan","Air Jordan 1 Retro High OG","Chicago Lost and Found","DZ5485-612","2022","Men","#c8102e","#f4efe6",
  [("8","310.00","New with box"),("11","335.00","New with box"),("14","299.00","Pre-owned")]),
 ("Jordan","Air Jordan 11 Retro","Gratitude","CT8012-170","2023","Men","#f7f7f7","#111111",
  [("10","235.00","New with box"),("12","240.00","New with box")]),
 ("Jordan","Air Jordan 4 Retro","Military Black","DH6927-111","2022","Men","#f2f2f2","#5a5a5a",
  [("11","185.00","Pre-owned")]),
 ("Nike","Dunk Low Retro","Panda","DD1391-100","2021","Men","#ffffff","#111111",
  [("7","115.00","New with box"),("9.5","120.00","New with box"),("11","118.00","New with box"),("15","140.00","New with box")]),
 ("Nike","Kobe 6 Protro","Grinch","CW2190-300","2020","Men","#5fd02b","#d42020",
  [("10","480.00","New with box"),("11.5","465.00","New with box")]),
 ("adidas","Yeezy Boost 350 V2","Bone","HQ6316","2022","Men","#ece7dc","#cfc7b4",
  [("9","230.00","New with box"),("10","235.00","New with box")]),
 ("New Balance","550","White Green","BB550WT1","2021","Men","#ffffff","#1f6f43",
  [("10.5","95.00","Pre-owned")]),
]

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">
<rect width="600" height="600" fill="#f3f1ed"/>
<path d="M70 360 C 90 300, 150 270, 210 262 L 260 230 C 290 212, 330 220, 345 250 C 360 285, 400 300, 455 315 C 510 330, 535 352, 535 378 L 535 395 L 70 395 Z" fill="{c1}" stroke="#222" stroke-width="6" stroke-linejoin="round"/>
<path d="M210 262 C 240 300, 300 320, 345 250" fill="none" stroke="{c2}" stroke-width="16" stroke-linecap="round"/>
<rect x="64" y="392" width="478" height="34" rx="12" fill="{c2}" stroke="#222" stroke-width="6"/>
<text x="300" y="490" font-family="Arial,Helvetica,sans-serif" font-size="30" font-weight="700" text-anchor="middle" fill="#9a8f80">SAMPLE PHOTO</text>
<text x="300" y="530" font-family="Arial,Helvetica,sans-serif" font-size="22" text-anchor="middle" fill="#9a8f80">{label}</text>
</svg>"""

items, n = [], 0
for brand, model, cw, sc, yr, dept, c1, c2, sizes in MODELS:
    img = f"{sc.lower()}.svg"
    with open(os.path.join(IMG_DIR, img), "w") as f:
        f.write(SVG.format(c1=c1, c2=c2, label=sc))
    for size, price, cond in sizes:
        n += 1
        iid = f"v1|SAMPLE{n:010d}|0"
        title = f"{model} {cw} {sc} Size {size} {'Mens' if dept=='Men' else dept} {'New' if cond.startswith('New') else 'Used'}"
        if brand == "adidas":
            title = "adidas " + title
        if brand == "Nike" and not model.startswith("Nike"):
            title = "Nike " + title
        items.append({
            "itemId": iid,
            "title": title[:80],
            "price": {"value": price, "currency": "USD"},
            "condition": cond,
            "image": {"imageUrl": f"/sample-img/{img}"},
            "itemWebUrl": f"https://www.ebay.com/itm/SAMPLE{n:010d}",
            "seller": {"username": "ukcats239"},
            "buyingOptions": ["FIXED_PRICE", "BEST_OFFER"],
            "shippingOptions": [{"shippingCostType": "FIXED", "shippingCost": {"value": "0.00" if float(price) >= 150 else "14.95", "currency": "USD"}}],
            "localizedAspects": [
                {"name": "Brand", "value": brand},
                {"name": "Model", "value": model},
                {"name": "Colorway", "value": cw},
                {"name": "Style Code", "value": sc},
                {"name": "US Shoe Size", "value": size},
                {"name": "Department", "value": dept},
                {"name": "Release Year", "value": yr},
            ],
        })

out = {
    "_SAMPLE_DATA": True,
    "_note": "SAMPLE DATA ONLY. Invented listings shaped like eBay Browse API itemSummaries "
             "(plus localizedAspects from getItem). Prices, item IDs and photos are NOT real. "
             "The live build replaces this automatically once EBAY_CLIENT_ID/EBAY_CLIENT_SECRET exist.",
    "seller_username": "ukcats239",
    "itemSummaries": items,
}
with open(os.path.join(HERE, "sample_listings.json"), "w") as f:
    json.dump(out, f, indent=1)

# A model that was in stock on an earlier (sample) run and has since sold out,
# so the sold-out page path is exercised on the very first build.
with open(os.path.join(IMG_DIR, "dn3707-100.svg"), "w") as f:
    f.write(SVG.format(c1="#ffffff", c2="#8a8d8f", label="DN3707-100"))
print(f"wrote {len(items)} sample listings")
