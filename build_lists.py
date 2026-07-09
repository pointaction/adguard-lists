#!/usr/bin/env python3
"""
build_lists.py  -  Point Action DNS list builder / curation helper.

Goal: "fork" HaGeZi Multi PRO into a single self-hosted master blocklist while
keeping YOUR hand-curated rules safe. Run it whenever you want to refresh from
upstream. Your rules live in pasblacklist.txt and are NEVER overwritten;
HaGeZi is merged UNDERNEATH them and de-duplicated.

    Edit  ->  pasblacklist.txt        (your rules; source of truth)
    Edit  ->  paswhitelist.txt        (your allow rules)
    Build ->  pasblacklist.built.txt  (personal + HaGeZi PRO; AdGuard loads THIS)

Usage:
    python3 build_lists.py                 # fetch HaGeZi PRO and build
    python3 build_lists.py --tier ultimate # use a different HaGeZi tier
    python3 build_lists.py --offline       # validate personal list only, no fetch
    python3 build_lists.py --check         # lint only, don't write output

Point AdGuard Home's blocklist source at pasblacklist.built.txt (or host it and
use the URL). Point the allowlist at paswhitelist.txt. When your own list is
mature enough, run with --offline and just serve pasblacklist.txt directly -
that's the fork fully graduating off HaGeZi.
"""

import argparse
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PERSONAL = os.path.join(HERE, "pasblacklist.txt")
WHITELIST = os.path.join(HERE, "paswhitelist.txt")
OUTPUT = os.path.join(HERE, "pasblacklist.built.txt")

# HaGeZi tiers (AdGuard/adblock format). PRO is the recommended base.
HAGEZI = {
    "light":    "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/light.txt",
    "normal":   "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/multi.txt",
    "pro":      "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/pro.txt",
    "pro.plus": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/pro.plus.txt",
    "ultimate": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/ultimate.txt",
}

# Pull the bare domain out of a rule so we can de-duplicate.
BLOCK_RE = re.compile(r"^\|\|([a-z0-9._-]+)\^")
ALLOW_RE = re.compile(r"^@@\|\|([a-z0-9._-]+)\^")
PLAIN_RE = re.compile(r"^([a-z0-9._-]+)$")


def domain_key(line):
    """Return the normalized domain a rule targets, or None."""
    for rx in (BLOCK_RE, ALLOW_RE):
        m = rx.match(line)
        if m:
            return m.group(1).lower()
    m = PLAIN_RE.match(line)
    if m and "." in m.group(1):
        return m.group(1).lower()
    return None


def lint(lines, label):
    """Warn about rules that silently do nothing in a DNS filter."""
    problems = []
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        if not s or s.startswith("!") or s.startswith("#"):
            continue
        if s.startswith("/") and s.endswith("/"):
            try:
                re.compile(s[1:-1])
            except re.error as e:
                problems.append(f"{label}:{i}  bad regex: {s}  ({e})")
            continue
        if s.startswith("@@/") and s.endswith("/"):
            continue
        # '://' or a path segment before the separator = ineffective in DNS
        head = s.split("^")[0]
        if "://" in s:
            problems.append(f"{label}:{i}  contains '://' (invalid): {s}")
        elif "/" in head and not head.startswith("@@/"):
            problems.append(f"{label}:{i}  path rule won't match in DNS: {s}")
    return problems


def load(path):
    if not os.path.exists(path):
        sys.exit(f"ERROR: missing {path}")
    with open(path, encoding="utf-8") as f:
        return f.read().splitlines()


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "pointaction-build/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace").splitlines()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="pro", choices=HAGEZI.keys())
    ap.add_argument("--offline", action="store_true", help="skip HaGeZi fetch")
    ap.add_argument("--check", action="store_true", help="lint only, no output file")
    args = ap.parse_args()

    personal = load(PERSONAL)
    whitelist = load(WHITELIST)

    # Lint both hand-edited files.
    problems = lint(personal, "pasblacklist") + lint(whitelist, "paswhitelist")
    if problems:
        print("LINT WARNINGS:")
        for p in problems:
            print("  " + p)
    else:
        print("Lint: clean.")

    if args.check:
        return

    # Everything you've already decided (block or allow) is "claimed".
    claimed = {k for k in (domain_key(l.strip()) for l in personal) if k}
    claimed |= {k for k in (domain_key(l.strip()) for l in whitelist) if k}

    out = list(personal)

    if not args.offline:
        url = HAGEZI[args.tier]
        print(f"Fetching HaGeZi {args.tier}: {url}")
        upstream = fetch(url)
        added = 0
        body = ["", f"! ==== HaGeZi {args.tier} (forked {url}) ===="]
        for raw in upstream:
            s = raw.strip()
            if not s or s.startswith("!") or s.startswith("#"):
                continue
            k = domain_key(s)
            if k and k in claimed:
                continue  # your rule already covers this domain
            if k:
                claimed.add(k)
            body.append(s)
            added += 1
        out += body
        print(f"Merged {added} upstream rules "
              f"({len(upstream)} fetched, {len(upstream) - added} skipped/dupes).")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"Wrote {OUTPUT}  ({len(out)} lines).")
    print("Point AdGuard Home's blocklist at this file; allowlist at paswhitelist.txt.")


if __name__ == "__main__":
    main()
