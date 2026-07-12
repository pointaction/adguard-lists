# adguard-lists

[![Validate](https://github.com/pointaction/adguard-lists/actions/workflows/validate-lists.yml/badge.svg)](https://github.com/pointaction/adguard-lists/actions/workflows/validate-lists.yml)
[![Sync allowlists](https://github.com/pointaction/adguard-lists/actions/workflows/sync-allowlists.yml/badge.svg)](https://github.com/pointaction/adguard-lists/actions/workflows/sync-allowlists.yml)
[![Sync blocklists](https://github.com/pointaction/adguard-lists/actions/workflows/sync-blocklists.yml/badge.svg)](https://github.com/pointaction/adguard-lists/actions/workflows/sync-blocklists.yml)
[![Check sources](https://github.com/pointaction/adguard-lists/actions/workflows/check-sources.yml/badge.svg)](https://github.com/pointaction/adguard-lists/actions/workflows/check-sources.yml)

DNS allowlists and blocklists for my network.

This repo hosts my allow/block lists in **AdGuard / Adblock Plus format**
(`@@||domain^` to allow, `||domain^` to block). The format works with both AdGuard
Home and **Technitium DNS Server**, which is what I run. Everything is hosted here on
GitHub.

Feel free to copy, use, or contribute.

## My network

```
📺💻📱  Clients
   │
   ▼
🖥️  Technitium DNS Server (Webmin + Configserver Firewall on Ubuntu 24.04) loads the lists in this repo
   │
   ▼
☁️  DNSSEC + DNS-over-TLS (Cloudflare)
   │
   ▼
🛜  TP-Link Omada ER605 Gateway + Smart Switch (VLANs)
   │
   ▼
🌐  Internet
```

## Current stats

<!-- STATS:START -->

_Last updated: 2026-07-12 18:07 UTC_

| List | Allow rules | Block rules |
|------|------------:|------------:|
| `pasallow-completewhitelist.txt` | 8,029 | — |
| `pasallow-h12-whitelist.txt` | 5,635 | — |
| `pasallow-referral.txt` | 1,542 | — |
| `pasblacklist.txt` | 11 | 176 |
| `pasblock-amazon.txt` | — | 359 |
| `pasblock-apple.txt` | — | 106 |
| `pasblock-completeblocklist.txt` | — | 936,342 |
| `pasblock-dandelion-sprout.txt` | — | 11,519 |
| `pasblock-gambling.txt` | — | 146,115 |
| `pasblock-haGeZi-pro.txt` | — | 232,335 |
| `pasblock-huawei.txt` | — | 135 |
| `pasblock-lgwebos.txt` | — | 340 |
| `pasblock-microsoft.txt` | — | 370 |
| `pasblock-native-oppo.txt` | — | 465 |
| `pasblock-nsfw.txt` | — | 107,807 |
| `pasblock-osid.txt` | — | 327,964 |
| `pasblock-roku.txt` | — | 71 |
| `pasblock-samsung.txt` | — | 189 |
| `pasblock-shadow-whisper.txt` | — | 43,201 |
| `pasblock-tif.txt` | — | 554,444 |
| `pasblock-tiktok.txt` | — | 424 |
| `pasblock-urlhaus.txt` | — | 12,340 |
| `pasblock-vivo.txt` | — | 227 |
| `pasblock-xiaomi.txt` | — | 347 |
| `paswhitelist.txt` | 98 | — |
| **Total (sum)** | **15,315** | **2,375,276** |
| **Total (unique domains)** | **13,443** | **1,092,721** |

<!-- STATS:END -->

## What's in this repo

### Allow lists (`@@||domain^`)

| File | What it is | Source |
|------|------------|--------|
| `paswhitelist.txt` | My allowlist — trusted services I never want blocked (WGU / remote proctoring, Roku Channel, personal domains, dev tools). | Hand-maintained |
| `pasreferral-whitelist.txt` | Affiliate / referral / tracking domains kept working so links in mail and search resolve. | Auto-synced daily from HaGeZi, converted to allow format |

### Block lists (`||domain^`)

| File | What it is | Source |
|------|------------|--------|
| `pasblacklist.built.txt` | My blocklist (streaming ads, telemetry) with a few inline `@@` allows for playback. | Built from my own rules |
| `pasblock-*.txt` | Category blocklists — one file per upstream source (tif, rebind, amazon, apple, gambling, huawei, lgwebos, microsoft, native-oppo, nsfw, roku, tiktok, vivo, xiaomi, samsung). | Auto-synced daily, cleaned & deduped |

### Scripts & config

| File | Purpose |
|------|---------|
| `validate_lists.py` | Validates every `.txt` list: syntax, within-file duplicates, and live DNS resolution. |
| `build_blocklist.py` | Normalizes a raw upstream list (hosts / adblock / plain) into clean `||domain^` rules, deduped, with my allow list subtracted. |
| `build_lists.py` | Builds `pasblacklist.built.txt` from my personal rules. |
| `blocklist-sources.txt` | Control panel for the blocklist sync — one `name url` line per source. |

## Automation (GitHub Actions)

Everything refreshes and self-checks automatically:

- **`validate-lists.yml`** — runs on every push/PR and weekly. Auto-discovers all `.txt`
  lists and fails if any rule is malformed or duplicated within a file.
- **`sync-referral-whitelist.yml`** — daily. Fetches HaGeZi's referral allowlist, converts
  the plain domains to `@@||domain^`, and commits `pasreferral-whitelist.txt`.
- **`sync-blocklists.yml`** — daily. For each source in `blocklist-sources.txt`, fetches it,
  normalizes to `||domain^`, dedupes, subtracts my allow-listed domains, and commits
  `pasblock-<name>.txt`. Timestamp-only changes are skipped so there are no empty commits.

## Adding a new list

**A new block source:** add one line to `blocklist-sources.txt` —

```
name https://example.com/somelist.txt
```

Commit it, then run **Actions → Sync blocklists → Run workflow**. A cleaned
`pasblock-name.txt` appears, ready to use.

## Using these in Technitium (or AdGuard Home)

Add the **raw** URL of each list to Technitium's *Block List URLs* box — **no `!`
prefix on any of them**. Because these are adblock format, Technitium auto-detects
`@@||domain^` as allow and `||domain^` as block per rule. Example:

```
https://raw.githubusercontent.com/pointaction/adguard-lists/main/paswhitelist.txt
https://raw.githubusercontent.com/pointaction/adguard-lists/main/pasreferral-whitelist.txt
https://raw.githubusercontent.com/pointaction/adguard-lists/main/pasblacklist.built.txt
https://raw.githubusercontent.com/pointaction/adguard-lists/main/pasblock-samsung.txt
...
```

Then **Settings → Blocking → Update Now** and confirm the Allow List / Block List
counts on the dashboard.
