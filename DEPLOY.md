# Deploying duckwalksneakers.com

## Setup: GitHub Actions builds, Cloudflare Pages hosts (both free)

Repo: **https://github.com/Skipcon1221/duckwalksneakers** (public).

GitHub Actions rebuilds the site from eBay **every 3 hours** (`.github/workflows/build.yml`) and uploads the
finished `site/` folder to a **Cloudflare Pages** project named `duckwalksneakers` (Direct Upload with
Cloudflare's official `cloudflare/wrangler-action`). Cloudflare serves it with free HTTPS on
duckwalksneakers.com. No server, no monthly bill.

**GitHub Pages stays OFF.** GitHub's Pages terms say Pages is not for sites "primarily directed at
facilitating commercial transactions". Cloudflare's terms have no such rule (see COMPLIANCE.md section 9).

Repo layout: the repo root is exactly this folder, so `build.py`, `config.json`, `duckwalk/`, `static/`,
`data/` and `.github/workflows/build.yml` sit at the top level. The default branch must be `main`.
Do not commit `site/`, `screenshots/` or any `.env` file (`.gitignore` already covers them).

Things to know
- The repo is public. The eBay and Cloudflare keys live only in encrypted repository *secrets*, never in the code.
- The only file the workflow commits back is `data/live/registry.json` (model names, URL slugs, dates and a
  change hash) plus `data/live/model_content.json`. No photos, prices, item IDs or buyer data are stored.
- GitHub can delay scheduled runs, sometimes by an hour at busy times. A 3-hour schedule leaves room under
  eBay's 6-hour rule, and every page shows "updated X hours ago" plus a red warning if data is over 6 hours old.
- GitHub pauses scheduled workflows in public repos after 60 days with no repo activity. Grok Bot checks the
  Actions tab weekly and presses "Run workflow" or re-enables it if it ever pauses.
- Cloudflare free-plan limits (https://developers.cloudflare.com/pages/platform/limits/): 20,000 files per
  site, 25 MiB per file, 500 *builds* per month, 100 custom domains per project. We upload a finished folder,
  so Cloudflare runs no build; even if every upload counted, 8 a day is about 248 a month. The site today is
  about 170 files and 3 MB.
- Old Shopify links (`/products/...`, `/collections/...`, `/pages/...`, `/cart`): Cloudflare Pages serves our
  top-level `404.html` for any path it can't find
  (https://developers.cloudflare.com/pages/configuration/serving-pages/#not-found-behavior), and that page
  sends visitors to the home page after about a second. Because `404.html` exists, Cloudflare does not switch
  to its "single-page app" mode. Never delete `404.html`.
- `site/CNAME` is no longer written (Cloudflare ignores it; the domain is set in the Pages project).
  `site/.nojekyll` is an empty file and harmless.

---

## What Mark does (one time)

1. **eBay developer keys** (already done; listed so the steps are complete)
   - Production keyset at https://developer.ebay.com, Marketplace Account Deletion opt-out done
     ("Not persisting eBay data"), and repo secrets `EBAY_CLIENT_ID` / `EBAY_CLIENT_SECRET` plus variable
     `EBAY_SELLER_USERNAME` = `ukcats239` are in place.
2. **Free Cloudflare account**: sign up at https://dash.cloudflare.com/sign-up (Free plan, no card needed for
   Pages).
3. **Cloudflare API token** (lets GitHub upload the site, nothing else):
   *My Profile* (or *Manage Account*), *API Tokens*, **Create Token**, *Custom token*, **Get started**.
   Name it `duckwalk-github-deploy`. Permissions: **Account / Cloudflare Pages / Edit**, and nothing else.
   Account resources: your account only. *Continue to summary*, **Create Token**, and copy the token once
   (Cloudflare only shows it once). Paste it straight into the GitHub secret in step 5; never paste it in chat.
4. **Account ID**: in the Cloudflare dashboard, *Workers & Pages* (or any domain's *Overview* page) shows
   **Account ID** on the right. It is not secret, but store it as a secret anyway.
5. **Add both to GitHub**: repo, *Settings*, *Secrets and variables*, *Actions*, *New repository secret*:
   - `CLOUDFLARE_API_TOKEN` = the token
   - `CLOUDFLARE_ACCOUNT_ID` = the account ID
6. **First deploy (creates the Pages project)**: repo, *Actions*, *Build & deploy duckwalksneakers.com*,
   **Run workflow**, tick *"First run only: create the Cloudflare Pages project"*, **Run workflow**.
   This creates the project `duckwalksneakers` with production branch `main` and uploads the site.
   Check it at **https://duckwalksneakers.pages.dev** (if Cloudflare says that name is taken, it adds a few
   letters; use the name it shows in *Workers & Pages*). Every later run (schedule, push, or Run workflow
   without the tick) just deploys.
7. **Custom domain** (do step 8 first if you pick option A): *Workers & Pages*, `duckwalksneakers`,
   *Custom domains*, **Set up a domain**, enter `duckwalksneakers.com`, *Continue*, confirm. Then do it
   again for `www.duckwalksneakers.com`. Cloudflare issues the HTTPS certificates itself. Do this in the Pages
   project first; a DNS record pointing at pages.dev without it gives a 522 error.
8. **DNS: pick one** (Grok Bot recommends **A**).

   The domain stays **registered at GoDaddy** either way (you keep renewing it there). Right now GoDaddy runs
   the DNS (nameservers `ns63.domaincontrol.com`, `ns64.domaincontrol.com`), there are no email (MX) or TXT
   records, and DNSSEC is off, so nothing else needs moving.

   **Old Shopify records to remove** (what is live today, checked Oct 27, 2026; Shopify's published values):
   | Type | Name | Value |
   |---|---|---|
   | A | @ | 23.227.38.65 |
   | AAAA | @ | 2620:0127:f00f:5:: (only if present; none showed up today) |
   | CNAME | www | shops.myshopify.com |
   Leave NS and SOA alone. If GoDaddy *Forwarding* is on for the domain, turn it off (except in option B).
   In Shopify, remove the domain from *Settings*, *Domains* so Shopify doesn't keep claiming it.

   **Option A (recommended): move DNS to Cloudflare, keep the registration at GoDaddy.** Needed if
   `duckwalksneakers.com` without www should work, because Cloudflare only serves a Pages site on the bare
   (apex) domain when the domain is a zone in the same Cloudflare account with its nameservers pointed at
   Cloudflare (https://developers.cloudflare.com/pages/configuration/custom-domains/#add-a-custom-apex-domain).
   a. Cloudflare dashboard, *Domains*, **Onboard a domain**, enter `duckwalksneakers.com`, pick the **Free**
      plan. When it shows the copied DNS records, **delete** the Shopify A (and any AAAA) on
      `duckwalksneakers.com` and the `www` CNAME to `shops.myshopify.com`.
   b. Cloudflare shows two nameservers (for example `xxx.ns.cloudflare.com`). Copy them exactly.
   c. GoDaddy: *My Products*, duckwalksneakers.com, *DNS*, **Nameservers**, *Change Nameservers*,
      *I'll use my own nameservers*, enter the two Cloudflare ones, save. (DNSSEC is already off; if GoDaddy
      ever says it's on, turn it off first.)
   d. Wait for Cloudflare's "your domain is active" email (usually under an hour, up to 24 hours).
   e. Do step 7. Cloudflare then adds the DNS records for both names itself (proxied, orange cloud).
   Rollback: set GoDaddy back to its default nameservers and re-add the Shopify records there.

   **Option B: keep GoDaddy DNS.** Works only for **www**, because GoDaddy can't put a CNAME on the bare
   domain and Cloudflare only gives the apex to its own zones.
   a. Step 7 with `www.duckwalksneakers.com` only.
   b. GoDaddy DNS: delete the Shopify A record on `@` (and any AAAA), then change the `www` CNAME from
      `shops.myshopify.com` to `duckwalksneakers.pages.dev`.
   c. GoDaddy *Forwarding* for `duckwalksneakers.com` to `https://www.duckwalksneakers.com` (301, forward only).
      GoDaddy's forwarding handles the bare domain, and HTTPS on the bare domain depends on GoDaddy.
   d. Tell Grok Bot so it changes `base_url` in `config.json` to `https://www.duckwalksneakers.com`
      (canonical tags and the sitemap must match the address people land on).
9. **After it's live**: open https://duckwalksneakers.com, a model page, and an old Shopify URL such as
   https://duckwalksneakers.com/products/test (should show "That page moved" and go to the home page).
10. Optional later: join eBay Partner Network and send Grok Bot the **Campaign ID**.

## eBay rules Mark has to follow on the eBay side (see COMPLIANCE.md)

- Never put duckwalksneakers.com (or any outside web address) in eBay listings, the store, the About page,
  or eBay messages. eBay's Links policy bans it even as plain text.
- Never put EPN affiliate links in your own listings, store or About page.
- Do not click or buy through your own EPN links, and do not ask friends to.
- Keep the eBay store name a name, not a web address (no ".com").

## What Grok Bot does

- Checks the first Cloudflare deploy on duckwalksneakers.pages.dev before DNS changes.
- Confirms DNS, HTTPS, the old-Shopify-link redirect and the 3-hour schedule work.
- Ongoing: writes verified `about` / `release_info` / `fit_notes` copy in `data/live/model_content.json`
  (no invented facts), watches the Actions log, adds the EPN campaign ID when you have one.

## Run it locally

```
python3 build.py --sample && cd site && python3 -m http.server 8000   # http://localhost:8000
EBAY_CLIENT_ID=... EBAY_CLIENT_SECRET=... python3 build.py           # live data
```

## Rollback

Option A: in GoDaddy, switch the nameservers back to GoDaddy's defaults and re-add the Shopify records
(A `@` 23.227.38.65, CNAME `www` shops.myshopify.com). Option B: re-add the same two records and turn off
forwarding. Nothing here is irreversible. The Cloudflare project can stay or be deleted.
