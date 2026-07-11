# adguard-lists

[![Validate](https://github.com/pointaction/adguard-lists/actions/workflows/validate-lists.yml/badge.svg)](https://github.com/pointaction/adguard-lists/actions/workflows/validate-lists.yml)
[![Sync allowlists](https://github.com/pointaction/adguard-lists/actions/workflows/sync-allowlists.yml/badge.svg)](https://github.com/pointaction/adguard-lists/actions/workflows/sync-allowlists.yml)
[![Sync blocklists](https://github.com/pointaction/adguard-lists/actions/workflows/sync-blocklists.yml/badge.svg)](https://github.com/pointaction/adguard-lists/actions/workflows/sync-blocklists.yml)
[![Check sources](https://github.com/pointaction/adguard-lists/actions/workflows/check-sources.yml/badge.svg)](https://github.com/pointaction/adguard-lists/actions/workflows/check-sources.yml)

Personal DNS allowlists and blocklists for my network.

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
🖥️  Technitium DNS Server  (Cockpit on Ubuntu 24.04 LTS)   ← loads the lists in this repo
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

_Stats are generated automatically on each sync._

<!-- STATS:END -->

## What's in this repo

### Allow lists (`@@||domain^`)

| File | What it is | Source |
|------|------------|--------|
| `paswhitelist.txt` | My personal allowlist — trusted services I never want blocked (WGU / remote proctoring, Roku Channel, personal domains, dev tools). | Hand-maintained |
| `pasreferral-whitelist.txt` | Affiliate / referral / tracking domains kept working so links in mail and search resolve. | Auto-synced daily from HaGeZi, converted to allow format |

### Block lists (`||domain^`)

| File | What it is | Source |
|------|------------|--------|
| `pasblacklist.built.txt` | My personal blocklist (streaming ads, telemetry) with a few inline `@@` allows for playback. | Built from my own rules |
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
