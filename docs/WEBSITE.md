# Website and app links

Canonical website: **https://finemenot.xyz/**. Sources, privacy and support are sections on this one barebones page: `#sources`, `#privacy`, `#support`. `App/AppLinks.swift` owns the app’s website and database base URLs.

The public page is written for drivers, with features, a six-step permission/setup guide, compatibility, troubleshooting, camera coverage, privacy and a legal disclaimer. Its maintainer and privacy contact is **Alonso Indacochea**. The Apple signing team's name is not the website's maintainer credit. Road Notice 1.0.4 is available free on the U.S. App Store as of September 25, 2026; the header links directly to https://apps.apple.com/us/app/road-notice/id6812094105 and states the U.S. availability and iOS 17 minimum. Release copy does not promise universal background/audio reliability.

Website and documentation updates use the existing Pages workflow and do not require a new iPhone build or App Store release.

`Scripts/stage_site.py` copies the canonical app icon from the asset catalog to `/app-icon.png`; the same file supplies the header, favicon and Apple touch icon. The website workflow watches the app-icon directory so future icon changes deploy automatically. Coverage figures are filled from the published summary, not edited into the page by hand.

The setup copy was checked against `SettingsView`, `MonitoringController`, `AlertPresenter`, the app entitlements, and Apple's current [location](https://support.apple.com/en-us/102515), [notifications](https://support.apple.com/guide/iphone/change-notification-settings-iph7c3d96bab/ios), [Focus](https://support.apple.com/guide/iphone/allow-or-silence-notifications-for-a-focus-iph21d43af5b/ios) and [Low Power Mode](https://support.apple.com/en-us/101604) guidance on September 15, 2026. Keep permission names and setup steps in sync with the app. Notifications support the visual warning and fallback sound; the siren uses direct media playback. Do not imply that allowing notifications guarantees background location, that every Focus offers the same controls, or that Silent-mode playback overrides zero media volume.

Cloudflare provides DNS, its reverse proxy and managed Universal SSL certificate. GitHub Pages hosts `Site/` and `Data/Published/`, deployed by the existing `data.yml` GitHub Action through `Scripts/stage_site.py`. No separate Worker, new hosting subscription or Codex automation is required.

DNS records are **proxied** CNAMEs, with automatic TTL:

| Name | Target |
|---|---|
| `finemenot.xyz` | `aindaco1.github.io` |
| `www.finemenot.xyz` | `aindaco1.github.io` |

Cloudflare flattens the apex CNAME. GitHub Pages is configured with `finemenot.xyz` as its custom domain and **Enforce HTTPS** enabled. Cloudflare uses **Full (strict)** origin encryption and **Always Use HTTPS**. TLS 1.3 and Automatic HTTPS Rewrites are enabled. Both the visitor-to-Cloudflare and Cloudflare-to-GitHub connections use valid certificates. `www` redirects to the apex, preserving the path. A green deployment alone does not establish DNS or HTTPS availability.

The setup was compared with the live `dustwave.xyz`, `shop.dustwave.xyz` and `pool.dustwave.xyz` GitHub Pages projects on September 14, 2026: all use Cloudflare proxying and HTTPS redirects. Those sites use the older Full encryption mode; Fine Me Not uses Full (strict) because its GitHub certificate is available. ZEMA (`zemabar.com`) independently demonstrates GitHub's managed certificate and HTTPS enforcement without the Cloudflare proxy.

Release checks: verify authoritative and public DNS; valid TLS without bypassing certificate checks; the page and its three section anchors; `/data/manifest.json`; the manifest’s immutable snapshot and SHA-256; and Update now in the new app build. TestFlight marketing/privacy URLs use the new domain. The owner explicitly requested no compatibility work for older test builds.

DNS is managed in Cloudflare; the website and data continue to deploy from GitHub Actions on the existing schedule. Do not remove the GitHub custom domain or rewrite app URLs independently of this contract.

`verify-website.yml` is a **manual-only**, read-only GitHub Action for migrations. It waits for valid public HTTPS and checks the canonical page, three section anchors, immutable snapshot digest/version/count and public database agreement. It has a bounded 65-minute job timeout and does not add a recurring schedule. Run `python3 Scripts/check_site.py` for the same delivery check without waiting. HTTPS enforcement is an administrator's Pages setting; the verification workflow does not receive an administrator credential.

Activation resolved September 14, 2026, at approximately 23:20 Mountain. After public DNS became available, GitHub was still serving a certificate without the custom hostname. Removing and immediately restoring the Pages custom domain restarted certificate provisioning, following [GitHub's documented recovery procedure](https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https#troubleshooting-certificate-provisioning-certificate-not-yet-created-error). GitHub then approved a certificate for the apex and `www`, expiring December 13, 2026, and HTTPS enforcement was enabled. Cloudflare's Universal SSL certificate is active with the same expiry date; renewal is provider-managed.

The [manual verification run](https://github.com/aindaco1/road-notice/actions/runs/34929772047) passed after the origin certificate became available. A subsequent local check through the Cloudflare proxy verified the page and all 2,695 records in `2026-09-14-352059fee0b5-23bbacd6`. Ordinary HTTPS requests validate successfully, HTTP redirects to HTTPS, and `www` redirects to the canonical host. Build 7 already uses these URLs; this server configuration fix needs no new app binary. Physical iPhone link and Update now acceptance remain device checks.
