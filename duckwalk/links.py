"""eBay link builders, eBay Partner Network (EPN) ready."""
import urllib.parse

# Standard EPN tracking params for ebay.com (EBAY-US rotation id 711-53200-19255-0).
EPN_PARAMS = {"mkcid": "1", "mkrid": "711-53200-19255-0", "siteid": "0", "toolid": "10001", "mkevt": "1"}


def epn(url, cfg, custom_id=""):
    camp = (cfg.get("epn_campaign_id") or "").strip()
    if not camp or not url:
        return url
    parts = urllib.parse.urlsplit(url)
    q = dict(urllib.parse.parse_qsl(parts.query))
    q.update(EPN_PARAMS)
    q["campid"] = camp
    if custom_id:
        q["customid"] = custom_id[:256]
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(q)))


def listing_url(listing, cfg):
    if cfg.get("epn_campaign_id") and listing.get("affiliate_url"):
        return listing["affiliate_url"]  # API-generated EPN link
    return epn(listing["url"], cfg, custom_id="dws-item")


def store_search_url(query, cfg, seller):
    if cfg.get("store_search_style") == "str" and cfg.get("ebay_store_url"):
        url = cfg["ebay_store_url"] + "?" + urllib.parse.urlencode({"_nkw": query})
    else:
        url = "https://www.ebay.com/sch/i.html?" + urllib.parse.urlencode({"_ssn": seller, "_nkw": query})
    return epn(url, cfg, custom_id="dws-store-search")


def store_home_url(cfg, seller):
    url = cfg.get("ebay_store_url") or "https://www.ebay.com/sch/i.html?" + urllib.parse.urlencode({"_ssn": seller})
    return epn(url, cfg, custom_id="dws-store")
