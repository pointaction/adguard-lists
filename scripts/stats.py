#!/usr/bin/env python3
"""
stats.py — Count entries in every pas*.txt list and write a stats table into
README.md between the markers:

    <!-- STATS:START -->
    ...table gets written here...
    <!-- STATS:END -->

Counts allow rules (@@||domain^) and block rules (||domain^) per file, plus
totals and total unique domains. Run with no arguments in the repo root.
"""

import datetime
import glob
import re
import sys

README = "README.md"
START = "<!-- STATS:START -->"
END = "<!-- STATS:END -->"

ALLOW_RE = re.compile(r"^@@\|\|([a-z0-9.*_-]+)\^", re.IGNORECASE)
BLOCK_RE = re.compile(r"^\|\|([a-z0-9.*_-]+)\^", re.IGNORECASE)


def count_file(path):
    allow, block = set(), set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            m = ALLOW_RE.match(line)
            if m:
                allow.add(m.group(1).lower())
                continue
            m = BLOCK_RE.match(line)
            if m:
                block.add(m.group(1).lower())
    return allow, block


def build_table():
    # All published list files live at the repo root as *.txt (the config files
    # were moved into build/, so root *.txt is only lists). This picks up
    # pas*.txt AND anything else like false-positive-fixes.txt.
    files = sorted(glob.glob("*.txt"))
    rows = []
    all_allow, all_block = set(), set()
    tot_allow = tot_block = 0
    for f in files:
        allow, block = count_file(f)
        all_allow |= allow
        all_block |= block
        tot_allow += len(allow)
        tot_block += len(block)
        a = f"{len(allow):,}" if allow else "—"
        b = f"{len(block):,}" if block else "—"
        rows.append(f"| `{f}` | {a} | {b} |")

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"_Last updated: {now}_",
        "",
        "| List | Allow rules | Block rules |",
        "|------|------------:|------------:|",
        *rows,
        f"| **Total (sum)** | **{tot_allow:,}** | **{tot_block:,}** |",
        f"| **Total (unique domains)** | **{len(all_allow):,}** | **{len(all_block):,}** |",
    ]
    return "\n".join(lines)


def main():
    try:
        with open(README, encoding="utf-8") as fh:
            text = fh.read()
    except FileNotFoundError:
        print(f"{README} not found", file=sys.stderr)
        return 1

    if START not in text or END not in text:
        print(f"Markers {START} / {END} not found in {README}", file=sys.stderr)
        return 1

    table = build_table()
    before = text.split(START)[0]
    after = text.split(END)[1]
    new = f"{before}{START}\n\n{table}\n\n{END}{after}"

    if new == text:
        print("Stats unchanged.")
        return 0

    with open(README, "w", encoding="utf-8") as fh:
        fh.write(new)
    print("README stats updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
