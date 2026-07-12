#!/usr/bin/env python3
"""
build_allowlist.py — Normalize a raw allowlist into clean AdGuard/Technitium
allow rules (`@@||domain^`).

Handles mixed input formats:
  - adblock allow, single pipe   @@|domain^      (e.g. BadBlock)
  - adblock allow, double pipe   @@||domain^
  - plain domain                 domain.com      (e.g. HaGeZi *-onlydomains)
  - hosts                        0.0.0.0 domain.com

It extracts domains, lowercases, drops comments/junk/block-rules/invalid lines,
de-duplicates, and emits one `@@||domain^` rule per line with a small header.

Usage:
  python build_allowlist.py RAW.txt --title "BadBlock" --source "https://..." > out.txt
"""

import argparse
import datetime
import re
import sys

DOMAIN_RE = re.compile(r"^(?:\*\.)?(?:[a-z0-9_-]+\.)+[a-z]{2,}$")
HOSTS_IP_RE = re.compile(r"^(?:0\.0\.0\.0|127\.0\.0\.1|::1?|::)$")
# @@ then one or two pipes, then the domain, then ^ (modifiers ignored).
ALLOW_RE = re.compile(r"^@@\|{1,2}([a-z0-9.*_-]+)\^", re.IGNORECASE)


def extract(line):
    """Return clean domains found on a single raw allowlist line (0 or more)."""
    line = line.strip()
    if not line or line[0] in "#!":
        return []

    m = ALLOW_RE.match(line)
    if m:
        cands = [m.group(1)]
    elif line.startswith("@@"):        # some other @@ form we don't parse
        return []
    elif line.startswith("||"):        # a block rule — not an allow entry
        return []
    else:
        parts = line.split()
        if not parts:
            return []
        if HOSTS_IP_RE.match(parts[0]):
            cands = parts[1:]
        elif len(parts) == 1:
            cands = parts
        else:
            return []

    out = []
    for c in cands:
        if c.startswith("#") or c.startswith("!"):
            break
        c = c.lower().rstrip(".")
        if DOMAIN_RE.match(c):
            out.append(c)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw", help="raw source file to clean")
    ap.add_argument("--title", default="Allowlist")
    ap.add_argument("--source", default="")
    args = ap.parse_args()

    domains = set()
    with open(args.raw, encoding="utf-8") as fh:
        for line in fh:
            for d in extract(line):
                domains.add(d)

    kept = sorted(domains)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"! Title: {args.title}")
    if args.source:
        print(f"! Source: {args.source}")
    print(f"! Synced: {now}")
    print(f"! Entries: {len(kept)}")
    print("!")
    for d in kept:
        print(f"@@||{d}^")
    return 0


if __name__ == "__main__":
    sys.exit(main())
