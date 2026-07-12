#!/usr/bin/env python3
"""
build_combined.py — Merge selected member lists into one curated combined feed.

Reads a combine-config (one member name per line). For each member it opens the
already-cleaned local file — pasblock-<name>.txt for block, pasallow-<name>.txt
for allow — validates that every rule is well-formed (FAILS the build on any
malformed rule), de-duplicates across all members, sorts, and writes the combined
output with an attributed header (each source credited with its URL, pulled from
the sources config).

Usage:
  python build_combined.py --kind block \
      --members blocklist-combine.txt --sources blocklist-sources.txt \
      --out pasblock-completeblocklist.txt \
      --title "Point Action Complete Blocklist"
"""

import argparse
import datetime
import os
import re
import sys

BLOCK_RE = re.compile(r"^\|\|[A-Za-z0-9_.*-]+\^(\$[^\s]*)?$")
ALLOW_RE = re.compile(r"^@@\|\|[A-Za-z0-9_.*-]+\^(\$[^\s]*)?$")
REGEX_RE = re.compile(r"^(@@)?/.+/(\$[^\s]*)?$")   # adblock regex rule


def read_members(path):
    names = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                names.append(s.split()[0])
    except FileNotFoundError:
        pass
    return names


def read_source_urls(path):
    urls = {}
    if not path:
        return urls
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                parts = s.split()
                if len(parts) >= 2:
                    urls[parts[0]] = parts[1]
    except FileNotFoundError:
        pass
    return urls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["block", "allow"], required=True)
    ap.add_argument("--members", required=True)
    ap.add_argument("--sources", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="Combined List")
    args = ap.parse_args()

    prefix = "pasblock-" if args.kind == "block" else "pasallow-"
    valid = BLOCK_RE if args.kind == "block" else ALLOW_RE

    members = read_members(args.members)
    urls = read_source_urls(args.sources)
    if not members:
        print(f"No members listed in {args.members} — nothing to combine.")
        return 1

    rules = set()
    errors = 0
    used = []
    for name in members:
        f = f"{prefix}{name}.txt"
        if not os.path.exists(f):
            print(f"  ✗ missing member file: {f} "
                  f"(add '{name}' to the sources config and sync it first)")
            errors += 1
            continue
        n = 0
        with open(f, encoding="utf-8") as fh:
            for i, raw in enumerate(fh, 1):
                s = raw.strip()
                if not s or s[0] in "!#[":
                    continue
                if valid.match(s) or REGEX_RE.match(s):
                    rules.add(s)
                    n += 1
                else:
                    print(f"  ✗ malformed {f}:{i}: {s!r}")
                    errors += 1
        used.append((name, n))
        print(f"  + {name}: {n} rules")

    if errors:
        print(f"FAILED: {errors} problem(s) — combined list not written.")
        return 1

    out = sorted(rules)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(f"! Title: {args.title}\n")
        fh.write("! Description: Curated combined feed built from the member lists below.\n")
        fh.write("! Homepage: https://github.com/pointaction/adguard-lists\n")
        fh.write(f"! Generated: {now}\n")
        fh.write(f"! Entries: {len(out)}\n")
        fh.write("!\n! Combined from — all credit to each list's maintainer:\n")
        for name, n in used:
            url = urls.get(name, "(see sources config)")
            fh.write(f"!   - {name} ({n:,} rules): {url}\n")
        fh.write("!\n! This is an opinionated personal aggregation provided as-is,\n")
        fh.write("! with no warranty. Use at your own risk.\n")
        fh.write("!\n")
        for r in out:
            fh.write(r + "\n")

    print(f"Wrote {len(out):,} unique rules to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
