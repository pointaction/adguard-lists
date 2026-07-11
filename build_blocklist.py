#!/usr/bin/env python3
"""
build_blocklist.py — Normalize a raw blocklist into a clean AdGuard/Technitium
block list.

Handles the three common upstream formats and mixes of them:
  - hosts        0.0.0.0 ads.example.com   (or 127.0.0.1 / :: prefixes)
  - adblock      ||ads.example.com^
  - plain domain ads.example.com

It extracts domains, lowercases, drops comments/junk/invalid lines, de-duplicates,
optionally subtracts an allow list, and emits one `||domain^` rule per line with a
small header.

Usage:
  python build_blocklist.py RAW.txt \
      --title "My Ads List" --source "https://..." [--allow allow_domains.txt] > out.txt

--allow takes a file of bare domains (one per line); any of those are removed from
the output so a source can't block something you've explicitly allowed.
"""

import argparse
import datetime
import re
import sys

# Bare-domain validator (optionally a leading *. wildcard label).
DOMAIN_RE = re.compile(r"^(?:\*\.)?(?:[a-z0-9_-]+\.)+[a-z]{2,}$")
HOSTS_IP_RE = re.compile(r"^(?:0\.0\.0\.0|127\.0\.0\.1|::1?|::)$")
ADBLOCK_RE = re.compile(r"^\|\|([a-z0-9.*_-]+)\^", re.IGNORECASE)


def extract(line):
    """Return a list of clean domains found on a single raw line (0 or more)."""
    line = line.strip()
    if not line or line[0] in "#!":
        return []
    if line.startswith("@@"):          # adblock allow rule — not a block entry
        return []

    m = ADBLOCK_RE.match(line)
    if m:
        cands = [m.group(1)]
    else:
        parts = line.split()
        if not parts:
            return []
        if HOSTS_IP_RE.match(parts[0]):
            cands = parts[1:]          # hosts format: everything after the IP
        elif len(parts) == 1:
            cands = parts              # plain domain
        else:
            return []

    out = []
    for c in cands:
        if c.startswith("#") or c.startswith("!"):
            break                      # start of an inline comment
        c = c.lower().rstrip(".")
        if DOMAIN_RE.match(c):
            out.append(c)
    return out


def load_allow(path):
    allow = set()
    if not path:
        return allow
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                d = line.strip().lower().rstrip(".")
                if d and not d.startswith(("#", "!")):
                    allow.add(d)
    except FileNotFoundError:
        pass
    return allow


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw", help="raw source file to clean")
    ap.add_argument("--title", default="Blocklist")
    ap.add_argument("--source", default="")
    ap.add_argument("--allow", default="", help="file of bare domains to exclude")
    args = ap.parse_args()

    allow = load_allow(args.allow)

    domains = set()
    with open(args.raw, encoding="utf-8") as fh:
        for line in fh:
            for d in extract(line):
                domains.add(d)

    kept = sorted(domains - allow)
    removed = len(domains) - len(kept)

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"! Title: {args.title}")
    if args.source:
        print(f"! Source: {args.source}")
    print(f"! Synced: {now}")
    print(f"! Entries: {len(kept)} (removed {removed} allow-listed)")
    print("!")
    for d in kept:
        print(f"||{d}^")

    # Nothing to fail on; a clean empty list is still valid.
    return 0


if __name__ == "__main__":
    sys.exit(main())
