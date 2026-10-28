# duckwalksneakers.com: auto-updating sneaker site

Static site generator (Python 3.10+, standard library only, nothing to install) that reads the
`ukcats239` eBay listings through eBay's official **Browse API** and publishes one page per sneaker
**model** (grouped by style code), with every in-stock size, price and photo, and "Buy on eBay" buttons.

```
python3 build.py             # live data if EBAY_CLIENT_ID + EBAY_CLIENT_SECRET are set, else SAMPLE data
python3 build.py --sample    # force the sample fixture
python3 build.py --preview   # show yellow PLACEHOLDER boxes for the content slots (never deploy this)
cd site && python3 -m http.server 8000   # look at it locally
```

| Path | What it is |
|---|---|
| `config.json` | Site name, seller username (`ukcats239`), store (`popsandus3`), EPN campaign ID (blank), category, max data age |
| `build.py` | Fetch → group → merge into the permanent registry → render `site/` |
| `duckwalk/ebay.py` | Client-credentials token, `item_summary/search?filter=sellers:{ukcats239}` (paginated), `getItem` / `get_items_by_item_group` for item specifics and multi-size listings, per-run call budget, nothing cached to disk |
| `duckwalk/models.py` | Style code / size / model parsing and grouping (item specifics first, title regex fallback) |
| `duckwalk/links.py` | eBay links, store-search links, EPN tracking params |
| `duckwalk/render.py` | HTML, meta tags, JSON-LD (Product + AggregateOffer, BreadcrumbList, WebSite) |
| `data/sample/` | **SAMPLE** fixture (invented listings, labeled `_SAMPLE_DATA: true`) + placeholder photos generator |
| `data/live/registry.json` | Every model ever seen: name, URL slug, dates, change hash. No photos, prices or item IDs. Slugs never change; pages are never deleted |
| `data/live/model_content.json` | Per-model copy slots (`about`, `release_info`, `fit_notes`). Empty = hidden on the live site |
| `.github/workflows/build.yml` | Rebuild on GitHub Actions every 3 hours, then deploy `site/` to Cloudflare Pages (Direct Upload with `cloudflare/wrangler-action`) |

Behavior
- **Sold out:** page stays at the same URL with a neutral image (the eBay photo and item specifics are dropped once the listing ends, per API License 8.1(b)(1)), shows "Sold out for now", links to a store search for that model and to 4 similar in-stock models. `Product` JSON-LD is dropped (only breadcrumbs) so Google doesn't show a stale price.
- **Freshness:** every page shows "Listings updated X hours ago" (computed in the browser). If the data is older than 6 hours, a red "may be out of date, confirm on eBay" note appears.
- **EPN:** set `epn_campaign_id` in `config.json` (or the `EPN_CAMPAIGN_ID` repo variable). Item links then use the API's `itemAffiliateWebUrl`, other eBay links get EPN params, links get `rel="sponsored"`, and the EPN disclosure ("As an eBay Partner Network Affiliate, we earn from qualifying purchases") appears at the top of every page and in the footer.
- **Sample safety:** sample builds show a yellow SAMPLE banner, are `noindex`, and robots.txt blocks crawling. CI sets `REQUIRE_LIVE=1` so it fails instead of publishing sample data.
- **Old Shopify links:** `/products/...`, `/collections/...` etc. land on a 404 page that sends visitors to the home page.
- **eBay content box:** photos, prices, sizes and item specifics from eBay sit in a labeled "From our live eBay listings" box, separate from our own copy (API License 8.1(b)(2)).
- **Privacy:** `/privacy/` page (API License 8.2(c)), footer links to it and to the eBay User Agreement.

See `COMPLIANCE.md` for the eBay terms review and `DEPLOY.md` for setup.
