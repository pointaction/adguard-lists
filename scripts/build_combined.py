#!/usr/bin/env python3
"""
build_combined.py — Merge many upstream lists into ONE curated combined feed.

Reads a sources config in the SAME format as blocklist-sources.txt
(one "<name> <url>" per line). The workflow fetches each URL into a raw dir
(one file per source name); this script reads those raw files, normalizes each
to clean domains (handles hosts / adblock / plain / @@| formats), de-duplicates
across all sources, optionally subtracts an allow list (block feeds), and writes
ONE combined output with a header crediting every source.

A source that failed to fetch is simply skipped — a dead upstream never breaks
the feed.

Usage:
  python build_combined.py --kind block \
      --sources build/combine-blocklist-sources.txt --rawdir _rawb \
      --allow allow_domains.txt --out pasblock-completeblocklist.txt \
      --title "Point Action Complete Blocklist"
"""

import argparse
import datetime
import os
import re
import sys

DOMAIN_RE = re.compile(r"^(?:\*\.)?(?:[a-z0-9_-]+\.)+(?:[a-z]{2,}|xn--[a-z0-9-]+)$")
HOSTS_IP_RE = re.compile(r"^(?:0\.0\.0\.0|127\.0\.0\.1|::1?|::)$")
BLOCK_ADBLOCK = re.compile(r"^\|\|([a-z0-9.*_-]+)\^", re.IGNORECASE)
ALLOW_ADBLOCK = re.compile(r"^@@\|{1,2}([a-z0-9.*_-]+)\^", re.IGNORECASE)


def clean(c):
    c = c.lower().rstrip(".")
    return c if DOMAIN_RE.match(c) else None


def extract_block(line):
    line = line.strip()
    if not line or line[0] in "#![":
        return []
    if line.startswith("@@"):
        return []
    m = BLOCK_ADBLOCK.match(line)
    if m:
        d = clean(m.group(1))
        return [d] if d else []
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
        if c.startswith(("#", "!")):
            break
        d = clean(c)
        if d:
            out.append(d)
    return out


def extract_allow(line):
    line = line.strip()
    if not line or line[0] in "#![":
        return []
    m = ALLOW_ADBLOCK.match(line)
    if m:
        d = clean(m.group(1))
        return [d] if d else []
    if line.startswith("@@") or line.startswith("||"):
        return []
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
        if c.startswith(("#", "!")):
            break
        d = clean(c)
        if d:
            out.append(d)
    return out


def read_sources(path):
    src = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                parts = s.split()
                if len(parts) >= 2:
                    src.append((parts[0], parts[1]))
    except FileNotFoundError:
        pass
    return src


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
    ap.add_argument("--kind", choices=["block", "allow"], required=True)
    ap.add_argument("--sources", required=True)
    ap.add_argument("--rawdir", required=True)
    ap.add_argument("--allow", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="Combined List")
    args = ap.parse_args()

    extract = extract_block if args.kind == "block" else extract_allow
    emit = (lambda d: f"||{d}^") if args.kind == "block" else (lambda d: f"@@||{d}^")

    sources = read_sources(args.sources)
    allow = load_allow(args.allow) if args.kind == "block" else set()

    domains = set()
    used = []
    missing = 0
    for name, url in sources:
        f = os.path.join(args.rawdir, name + ".txt")
        if not os.path.exists(f) or os.path.getsize(f) == 0:
            print(f"  ⚠ skipping (not fetched): {name}")
            missing += 1
            continue
        n = 0
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                for d in extract(line):
                    domains.add(d)
                    n += 1
        used.append((name, url, n))
        print(f"  + {name}: {n} raw domains")

    kept = sorted(domains - allow)
    removed = len(domains) - len(kept)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(f"! Title: {args.title}\n")
        fh.write("! Description: Curated combined feed. All credit to each source's maintainer.\n")
        fh.write("! Homepage: https://github.com/pointaction/adguard-lists\n")
        fh.write(f"! Generated: {now}\n")
        fh.write(f"! Entries: {len(kept)}\n")
        if args.kind == "block":
            fh.write(f"! Allow-listed domains removed: {removed}\n")
        fh.write("!\n! Combined from:\n")
        for name, url, n in used:
            fh.write(f"!   - {name}: {url}\n")
        if missing:
            fh.write(f"! ({missing} source(s) unreachable this run — skipped)\n")
        fh.write("!\n! Provided as-is with no warranty. Use at your own risk.\n!\n")
        for d in kept:
            fh.write(emit(d) + "\n")

    print(f"Wrote {len(kept):,} unique rules to {args.out} "
          f"({len(used)} sources merged, {missing} skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
