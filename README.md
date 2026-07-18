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
🖥️  Technitium DNS Server  (Webmin with CSF on Ubuntu 24.04 LTS) ← loads the lists in this repo
   │
   ▼
☁️  DNSSEC + DNS-over-TLS  (Cloudflare)
   │
   ▼
🛜  TP-Link Omada ER605 Gateway + Smart Switch (VLANs)
   │
   ▼
🌐  Internet
```

## Current stats

<!-- STATS:START -->

_Last updated: 2026-07-18 14:34 UTC_

| List | Allow rules | Block rules |
|------|------------:|------------:|
| `false-positive-fixes.txt` | 222 | — |
| `pas-shipping-carrier-whitelist.txt` | 21 | — |
| `pasallow-completewhitelist.txt` | 8,035 | — |
| `pasallow-referral.txt` | 1,548 | — |
| `pasblacklist.txt` | — | 263 |
| `pasblock-adway.txt` | — | 6,469 |
| `pasblock-amazon.txt` | — | 360 |
| `pasblock-apple.txt` | — | 107 |
| `pasblock-completeblocklist.txt` | — | 987,136 |
| `pasblock-dandelion-sprout.txt` | — | 11,519 |
| `pasblock-gambling.txt` | — | 156,004 |
| `pasblock-haGeZi-pro++.txt` | — | 271,780 |
| `pasblock-huawei.txt` | — | 135 |
| `pasblock-lgwebos.txt` | — | 340 |
| `pasblock-microsoft.txt` | — | 386 |
| `pasblock-native-oppo.txt` | — | 468 |
| `pasblock-nsfw.txt` | — | 112,224 |
| `pasblock-osid.txt` | — | 327,412 |
| `pasblock-roku.txt` | — | 71 |
| `pasblock-samsung.txt` | — | 202 |
| `pasblock-shadow-whisper.txt` | — | 43,246 |
| `pasblock-tif.txt` | — | 552,075 |
| `pasblock-tiktok.txt` | — | 425 |
| `pasblock-urlhaus.txt` | — | 11,616 |
| `pasblock-vivo.txt` | — | 227 |
| `pasblock-xiaomi.txt` | — | 347 |
| `paswhitelist.txt` | 16 | — |
| **Total (sum)** | **9,842** | **2,482,812** |
| **Total (unique domains)** | **8,258** | **1,156,041** |

<!-- STATS:END -->

## What's in this repo

### Allow lists (`@@||domain^`)

| File | What it is | Source |
|------|------------|--------|
| `paswhitelist.txt` | My allowlist — trusted services I never want blocked. | Hand-maintained |
| `pasreferral-whitelist.txt` | Affiliate / referral / tracking domains kept working so links in mail and search resolve. | Auto-synced daily from HaGeZi, converted to allow format |
| `false-positive-fixes.txt` | A privacy-respecting allowlist that fixes legitimate breakage caused by DNS blocklists — WITHOUT re-enabling ads, analytics, or tracking. | Hand-maintained |

### Block lists (`||domain^`)

| File | What it is | Source |
|------|------------|--------|
| `pasblock-*.txt` | Category blocklists — one file per upstream source (tif, rebind, amazon, apple, gambling, huawei, lgwebos, microsoft, native-oppo, nsfw, roku, tiktok, vivo, xiaomi, samsung). | Auto-synced daily, cleaned & deduped |

### Scripts & config

| File | Purpose |
|------|---------|
| `changelog.py` | Turn a git diff of the list files into a dated CHANGELOG entry. |
| `stats.py` | Count entries in every pas*.txt list and write a stats table into README.md between the markers. |
| `validate_lists.py` | Validates every `.txt` list: syntax, within-file duplicates, and live DNS resolution. |
| `build_blocklist.py` | Normalize a raw blocklist into a clean AdGuard/Technitium block list. |
| `build_allowlist.py` | Normalize a raw allowlist into clean AdGuard/Technitium allow rules (`@@||domain^`). |
| `build_combined.py` | Merge many upstream lists into ONE curated combined feed. |
| `blocklist-sources.txt` | Control panel for the blocklist sync — one `name url` line per source. |
| `whitelist-sources.txt` | Control panel for the whitelist sync — one `name url` line per source. |
| `combine-blocklist-sources.txt` | Control panel for the Sources merged into the combined blocklist sync — one `name url` line per source. |
| `combine-whitelist-sources.txt` | Control panel for the Sources merged into the combined whitelist sync — one `name url` line per source. |

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
https://raw.githubusercontent.com/pointaction/adguard-lists/main/pasblacklist.txt
https://raw.githubusercontent.com/pointaction/adguard-lists/main/pasblock-samsung.txt
...
```

Then **Settings → Blocking → Update Now** and confirm the Allow List / Block List
counts on the dashboard.

## Disclaimer

These lists are a personal project, provided **as-is and with no warranty** of any
kind. DNS filtering can break websites, apps, and devices in ways that are hard to
predict. You are responsible for what you load on your own network — test before you
rely on it, and use at your own risk. Nothing here is affiliated with, endorsed by,
or supported by any of the upstream projects credited below, nor by AdGuard,
Technitium, or any listed service.

The combined feeds (`pasblock-completeblocklist.txt`, `pasallow-completewhitelist.txt`)
are convenience aggregations. The **individual upstream projects are the authoritative
source** — if you want the canonical, maintained version of any list, get it from its
own project rather than from here.
