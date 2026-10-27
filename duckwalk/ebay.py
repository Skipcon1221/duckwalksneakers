"""eBay data sources: official Browse API (live) or the labeled SAMPLE fixture.

Live mode uses only eBay's public Buy > Browse API with an application
(client-credentials) token. It never logs in as the seller and never scrapes.
"""
import base64
import json
import os
import time
import urllib.parse
import urllib.request

TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
ITEM_URL = "https://api.ebay.com/buy/browse/v1/item/"
SCOPE = "https://api.ebay.com/oauth/api_scope"


def _http(req, retries=3):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:500]
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 ** attempt * 2)
                continue
            raise RuntimeError(f"eBay API HTTP {e.code}: {body}") from None
        except urllib.error.URLError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt * 2)
                continue
            raise


def get_app_token(client_id, client_secret):
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = urllib.parse.urlencode({"grant_type": "client_credentials", "scope": SCOPE}).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST", headers={
        "Authorization": f"Basic {basic}",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    return _http(req)["access_token"]


def _headers(token, cfg):
    h = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": cfg.get("ebay_marketplace_id", "EBAY_US"),
        "Accept": "application/json",
    }
    camp = (cfg.get("epn_campaign_id") or "").strip()
    if camp:
        # Makes the API return itemAffiliateWebUrl (EPN tracking link) per item.
        h["X-EBAY-C-ENDUSERCTX"] = f"affiliateCampaignId={camp}"
    return h


def search_seller_items(token, cfg, seller, stats=None):
    """Every active listing for the seller, paginated (max 200 per page)."""
    items, offset, limit = [], 0, 200
    pages = 0
    while True:
        params = {
            "filter": f"sellers:{{{seller}}}",
            "limit": str(limit),
            "offset": str(offset),
        }
        if cfg.get("ebay_category_ids"):
            params["category_ids"] = cfg["ebay_category_ids"]
        url = SEARCH_URL + "?" + urllib.parse.urlencode(params)
        data = _http(urllib.request.Request(url, headers=_headers(token, cfg)))
        pages += 1
        page = data.get("itemSummaries", []) or []
        items.extend(page)
        total = data.get("total", 0)
        if stats is not None:
            stats["search_total"], stats["search_pages"] = total, pages
        offset += limit
        if not page or offset >= total or offset >= 10000:
            break
    return items


def get_item_aspects(token, cfg, item_id):
    url = ITEM_URL + urllib.parse.quote(item_id, safe="")
    data = _http(urllib.request.Request(url, headers=_headers(token, cfg)))
    return data.get("localizedAspects", []) or []


GROUP_URL = "https://api.ebay.com/buy/browse/v1/item/get_items_by_item_group"


def get_item_group(token, cfg, group_id):
    url = GROUP_URL + "?" + urllib.parse.urlencode({"item_group_id": group_id})
    return _http(urllib.request.Request(url, headers=_headers(token, cfg))).get("items", []) or []


def _availability(item):
    """IN_STOCK / LIMITED_STOCK / OUT_OF_STOCK / UNKNOWN from getItem-style estimatedAvailabilities."""
    ea = item.get("estimatedAvailabilities") or []
    if not ea:
        return "UNKNOWN"
    st = {a.get("estimatedAvailabilityStatus") for a in ea}
    if st & {"IN_STOCK", "LIMITED_STOCK"}:
        return "IN_STOCK"
    if any((a.get("estimatedAvailableQuantity") or 0) > 0 for a in ea):
        return "IN_STOCK"
    if "OUT_OF_STOCK" in st:
        return "OUT_OF_STOCK"
    return "UNKNOWN"


def load_live(cfg):
    """Fetch the seller's active listings.

    Nothing fetched here is written to disk: item specifics are looked up fresh on
    every run and kept only in memory (API License 3.1(b): intermediate copies are
    deleted when no longer needed). A per-run call budget keeps the app well under
    the default Browse API limit (5,000 calls/day) at 8 runs/day.
    """
    cid, secret = os.environ["EBAY_CLIENT_ID"], os.environ["EBAY_CLIENT_SECRET"]
    seller = os.environ.get("EBAY_SELLER_USERNAME") or cfg["ebay_seller_username"]
    budget = int(cfg.get("max_detail_calls_per_run", 450))
    token = get_app_token(cid, secret)
    stats = {}
    summaries = search_seller_items(token, cfg, seller, stats)
    calls = 1 + stats.get("search_pages", 1)
    stats["summaries"] = len(summaries)
    stats["summaries_with_group"] = sum(1 for it in summaries if it.get("itemGroupHref") or it.get("itemGroupId"))
    stats["summaries_with_group_type"] = sum(1 for it in summaries if it.get("itemGroupType"))
    stats["distinct_item_ids"] = len({it.get("itemId") for it in summaries})
    stats["group_sizes"], stats["singles"], stats["skipped_dupe_group"] = [], 0, 0
    stats["getitem_calls"], stats["group_calls"], stats["over_budget"] = 0, 0, 0
    stats["avail"] = {}

    items, seen = [], set()
    for it in summaries:
        gid = it.get("itemGroupId") or (it.get("itemGroupHref") and
              urllib.parse.parse_qs(urllib.parse.urlsplit(it["itemGroupHref"]).query).get("item_group_id", [None])[0])
        if gid and it.get("itemGroupType"):
            # Multi-size listing: expand into one entry per size variation.
            if gid in seen:
                stats["skipped_dupe_group"] += 1
                continue
            seen.add(gid)
            if calls < budget:
                try:
                    group_items = get_item_group(token, cfg, gid)
                    calls += 1
                    stats["group_calls"] += 1
                    stats["group_sizes"].append(len(group_items))
                    for gi in group_items:
                        stats["avail"][_availability(gi)] = stats["avail"].get(_availability(gi), 0) + 1
                        if _availability(gi) == "OUT_OF_STOCK":
                            continue  # sold-out size in a multi-size listing: don't show it as in stock
                        if not gi.get("shippingOptions"):
                            gi["shippingOptions"] = it.get("shippingOptions")
                        items.append(gi)  # full items already include localizedAspects
                    continue
                except Exception as e:
                    print(f"  warn: item group {gid} failed: {e}")
            else:
                stats["over_budget"] += 1
            items.append(it)
            continue
        if cfg.get("fetch_item_details", True) and calls < budget:
            try:
                it["localizedAspects"] = get_item_aspects(token, cfg, it["itemId"])
                calls += 1
                stats["getitem_calls"] += 1
            except Exception as e:  # one bad item shouldn't kill the build
                print(f"  warn: getItem {it['itemId']} failed: {e}")
        elif cfg.get("fetch_item_details", True):
            stats["over_budget"] += 1
        stats["singles"] += 1
        items.append(it)
    gs = stats.pop("group_sizes")
    # Counts only (no listing data) so a short build log can explain the numbers.
    print(f"  search: total={stats.get('search_total')} summaries={stats['summaries']} "
          f"distinct_ids={stats['distinct_item_ids']} pages={stats.get('search_pages')} "
          f"with_group={stats['summaries_with_group']} with_group_type={stats['summaries_with_group_type']}")
    print(f"  detail: group_calls={stats['group_calls']} variations={sum(gs)} "
          f"(min {min(gs) if gs else 0}, max {max(gs) if gs else 0}) dupe_group_summaries_skipped={stats['skipped_dupe_group']} "
          f"singles={stats['singles']} getitem_calls={stats['getitem_calls']} over_budget={stats['over_budget']}")
    print(f"  variation availability: {stats['avail']} (OUT_OF_STOCK sizes are not shown)")
    print(f"  {calls} eBay API calls this run (budget {budget})")
    return items, seller


def load_sample(path):
    with open(path) as f:
        data = json.load(f)
    assert data.get("_SAMPLE_DATA") is True, "fixture must be labeled sample"
    return data["itemSummaries"], data["seller_username"]


def live_credentials_present():
    return bool(os.environ.get("EBAY_CLIENT_ID") and os.environ.get("EBAY_CLIENT_SECRET"))
