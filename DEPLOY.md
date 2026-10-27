# Deploying duckwalksneakers.com

## Setup: GitHub Pages + a scheduled GitHub Action (free)

Repo: **https://github.com/Skipcon1221/duckwalksneakers** (public, created empty by Mark).

GitHub stores the code, rebuilds the site from eBay **every 3 hours** (`.github/workflows/build.yml`),
and hosts it with free HTTPS on duckwalksneakers.com. No server, no monthly bill.

Repo layout: the repo root is exactly this folder, so `build.py`, `config.json`, `duckwalk/`, `static/`,
`data/` and `.github/workflows/build.yml` sit at the top level. The default branch must be `main`.
Do not commit `site/`, `screenshots/` or any `.env` file (`.gitignore` already covers them).

Things to know
- The repo is public. The eBay keys live only in encrypted repository *secrets*, never in the code.
- The only file the workflow commits back is `data/live/registry.json` (model names, URL slugs, dates and a
  change hash) plus `data/live/model_content.json`. No photos, prices, item IDs or buyer data are stored.
- GitHub can delay scheduled runs, sometimes by an hour at busy times. A 3-hour schedule leaves room under
  eBay's 6-hour rule, and every page shows "updated X hours ago" plus a red warning if data is over 6 hours old.
- GitHub pauses scheduled workflows in public repos after 60 days with no repo activity. Grok Bot checks the
  Actions tab weekly and presses "Run workflow" or re-enables it if it ever pauses.

---

## What Mark does (one time)

1. **eBay developer keys**
   - Sign up at https://developer.ebay.com with your normal eBay login.
   - *Application Keysets*: create a **Production** keyset.
   - *Marketplace Account Deletion*: eBay requires you to subscribe or opt out **before the first production
     call**. Opt out: turn on "Not persisting eBay data" and pick the exemption reason that fits. Accurate
     description to use: "Shows only my own active eBay listings on my own catalog site. No data about any
     eBay buyer or other eBay user is collected or stored. Listing data is fetched fresh every run and not
     kept; only my own model names and page URLs are saved."
   - Send the **App ID (Client ID)** and **Cert ID (Client Secret)** through the secure form Grok Bot sends.
     Never paste them into chat.
2. **Add the keys**: repo, *Settings*, *Secrets and variables*, *Actions*:
   - Secrets: `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`
   - Variables: `EBAY_SELLER_USERNAME` = `ukcats239` (and later `EPN_CAMPAIGN_ID`)
3. **Turn on Pages**: repo, *Settings*, *Pages*, *Source: GitHub Actions*. Custom domain:
   `duckwalksneakers.com`, Save. (With Actions deploys, GitHub uses this setting, not the CNAME file.)
   Recommended: your GitHub profile *Settings*, *Pages*, *Add a domain* to verify duckwalksneakers.com.
4. **GoDaddy DNS**: godaddy.com, *My Products*, duckwalksneakers.com, **DNS**, *DNS Records*.

   **Delete** the old Shopify records (check the values match first; these are the usual Shopify ones):
   | Type | Name | Value |
   |---|---|---|
   | A | @ | 23.227.38.65 |
   | CNAME | www | shops.myshopify.com |
   (Delete any other A / AAAA records on `@` too. Leave NS, MX and SOA records alone.)

   **Add**:
   | Type | Name | Value | TTL |
   |---|---|---|---|
   | A | @ | 185.199.108.153 | 1 hour |
   | A | @ | 185.199.109.153 | 1 hour |
   | A | @ | 185.199.110.153 | 1 hour |
   | A | @ | 185.199.111.153 | 1 hour |
   | CNAME | www | `skipcon1221.github.io` | 1 hour |
   | TXT | `_github-pages-challenge-Skipcon1221` | (the code GitHub shows you) | 1 hour |

   If GoDaddy has *Forwarding* turned on for the domain, turn it off.
5. **After 30 to 60 minutes**: *Settings*, *Pages*, tick **Enforce HTTPS**.
6. Optional later: join eBay Partner Network and send Grok Bot the **Campaign ID**.

## eBay rules Mark has to follow on the eBay side (see COMPLIANCE.md)

- Never put duckwalksneakers.com (or any outside web address) in eBay listings, the store, the About page,
  or eBay messages. eBay's Links policy bans it even as plain text.
- Never put EPN affiliate links in your own listings, store or About page.
- Do not click or buy through your own EPN links, and do not ask friends to.
- Keep the eBay store name a name, not a web address (no ".com").

## What Grok Bot does

- Pushes this project to the repo, runs the first build with live data, and checks the live pages before DNS.
- Confirms DNS, HTTPS and the 3-hour schedule work.
- Ongoing: writes verified `about` / `release_info` / `fit_notes` copy in `data/live/model_content.json`
  (no invented facts), watches the Actions log, adds the EPN campaign ID when you have one.

## Run it locally

```
python3 build.py --sample && cd site && python3 -m http.server 8000   # http://localhost:8000
EBAY_CLIENT_ID=... EBAY_CLIENT_SECRET=... python3 build.py           # live data
```

## Rollback

Re-add the old Shopify records in GoDaddy. Nothing here is irreversible.
