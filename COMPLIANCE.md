# eBay terms review for duckwalksneakers.com (Oct 26, 2026)

Plain verdict: **the site code is compliant with the changes made below. One real risk is left: eBay says
production use of the Buy APIs (Browse included) needs an extra license through eBay Partner Network (EPN).
Do not go live on the Browse API until that is sorted.** This is a careful reading of the terms, not legal advice.

## 1. Browse API production access (REAL RISK, open)
- Buy APIs Requirements, https://developer.ebay.com/api-docs/buy/static/buy-requirements.html :
  "The use of eBay's Buy APIs in production is intended for eBay partners only. You must apply for production
  access through the eBay Partner Network." The process: EPN account, Buy API Application, mocks, EPN approval,
  then a developer support ticket "Buy API Production Access (eBay user ID)", then contracts.
- API call limits page (Wayback copy of 2026-06-13): "Buy APIs require an additional license."
- Counterpoint: EPN's Australian developer page says "EDP Browse API ... do not require additional approval"
  for EPN members (https://partnernetwork.ebay.com.au/page/developer-questionnaire). US practice is unclear.
- Needed: Mark joins EPN and applies for Buy API access for this use, using the screenshots as mocks.
  Fallback if refused: read his listings with the Trading API (GetSellerList) and his own sign-in token,
  which is not a Buy API. That is a code change.

## 2. API License Agreement (compliant with changes)
Official page blocks automated reads. Checked a Wayback copy (2026-08-08) plus a 2025-09-03 mirror; same text.
- 8.1(b)(1) "When the eBay Content is no longer publicly available, you must delete it from your Application."
  Change: sold-out pages no longer show or store the eBay photo or item specifics; registry keeps only name,
  slug, search words, dates and a hash.
- 8.1(b)(2) "eBay Content in a Public Display may not be co-mingled or combined with non-eBay Content."
  Change: all eBay data sits in a labeled "From our live eBay listings" box; our own copy is in a separate block.
- 8.1(c) listing info "may not be more than six (6) hours older"; if not, "disclose ... how much older".
  Change: rebuild every 3 hours (was 4). The "updated X hours ago" line and the over 6 hours warning stay.
- 3.1(b) intermediate copies "must be deleted when they are no longer required."
  Change: no item cache on disk; details fetched fresh each run and dropped.
- 8.2(c) "You must make publicly available ... an appropriate privacy policy." Change: /privacy/ page.
- Call limits: Browse default 5,000 calls/day. Change: per-run budget (450) so 8 runs stay near 3,600.
- 9.14 no infringing or misleading use: footer says the site is not run, endorsed or sponsored by eBay.

## 3. Logos and "Buy on eBay" (compliant, small residual risk)
- User Agreement: "The name "eBay" and other eBay marks, logos ... may not be used without the express written
  prior permission of eBay." https://www.ebay.com/help/policies/member-behavior-policies/user-agreement?id=4259
- The site uses no eBay logo and no eBay styling. "Buy on eBay" is plain text that says where the sale happens.
  The eBay logo requirement in the Buy API docs is for checkout integrations only. Kept as is.

## 4. Images (compliant)
Photos are hotlinked from eBay's image servers, never downloaded or stored. Sold-out pages show a neutral image.

## 5. Marketplace account deletion (compliant if Mark opts out correctly)
https://developer.ebay.com/marketplace-account-deletion : developers "must subscribe to or opt out ... before
they make their first production API call." The site stores no data about any eBay user. See DEPLOY.md step 1.

## 6. Links policy and offers outside eBay (compliant; rules for Mark)
- Links policy: listings "can't contain links that direct customers to a site other than eBay, even if the link
  is not clickable." https://www.ebay.com/help/policies/listing-policies/links-policy?id=4248
- Offers outside eBay: "Offering to buy or sell outside of eBay is not allowed." No checkout, prices or offers
  off eBay exist on this site. https://www.ebay.com/help/policies/payment-policies/offers-buy-sell-outside-ebay-policy?id=4272
- Mark must never put duckwalksneakers.com in listings, store, About page or messages.

## 7. EPN (compliant while off; approval needed before turning on)
https://partnernetwork.ebay.com/legal (published Sept 24, 2026)
- Disclosure must be clear and prominent. Change: when a campaign ID is set, a banner at the top of every page
  says "As an eBay Partner Network Affiliate, we earn from qualifying purchases."
- "Promotional Content created by a developer's program tool or API" is a restricted method that needs EPN's
  prior written approval. Leave `epn_campaign_id` blank until EPN approves this site.
- Own listings are OK to link (eBay UK EPN help: links "can direct your users to specific eBay listings
  (including your own)"). Clicking your own links is prohibited. No EPN links inside eBay listings or store.

## 8. Domain and brand names (compliant)
EPN bans domains that use eBay marks or end in "Bay". duckwalksneakers does neither. Sneaker brand names are
used only to describe the real items; footer says we are not affiliated. No federal trademark search was run on
"duckwalk".

## 9. Hosting: Cloudflare Pages, not GitHub Pages (checked Oct 27, 2026)
- GitHub Pages is off: GitHub's Pages terms say it is not meant for sites "primarily directed at facilitating
  commercial transactions". GitHub Actions is still used only to build.
- Cloudflare Self-Serve Subscription Agreement (https://www.cloudflare.com/terms/) has no ban on commercial
  sites on free plans. The one Free-plan rule that touches selling is 2.2.1(h): do not "process or collect
  personal or business credit card information on any web property that is receiving Free Services".
  This site has no checkout, forms or payments (all buying happens on eBay), so it complies. Keep it that way.
- Developer Platform terms (https://www.cloudflare.com/service-specific-terms-developer-platform/, Pages
  included) allow hosting content; they only bar illegal/harmful content, malware, phishing and project
  names that use other businesses' names deceptively. "duckwalksneakers" is our own name.
- Privacy page now names Cloudflare as the host and links its privacy policy (API License 8.2(c)).
