#!/usr/bin/env python3
"""
changelog.py — Turn a git diff of the list files into a dated CHANGELOG entry.

Reads a `git diff` (unified=0) on stdin, extracts added/removed domains from
allow (@@||domain^) and block (||domain^) rules, and PREPENDS a dated section
to CHANGELOG.md. Does nothing if there were no rule changes.

Typical use (in a workflow):
  git diff --unified=0 HEAD~1 HEAD -- 'pas*.txt' | python changelog.py
"""

import datetime
import re
import sys

CHANGELOG = "CHANGELOG.md"
MARKER = "<!-- CHANGELOG:TOP -->"
HEADER = (
    "# Changelog\n\n"
    "_Domains added and removed automatically by the sync workflows._\n\n"
    f"{MARKER}\n"
)
RULE_RE = re.compile(r"^([+-])(@@\|\||\|\|)([a-z0-9.*_-]+)\^", re.IGNORECASE)
SAMPLE = 15   # how many example domains to show per bucket


def parse(diff):
    added, removed = set(), set()
    for line in diff.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        m = RULE_RE.match(line)
        if not m:
            continue
        sign, kind, domain = m.group(1), m.group(2), m.group(3).lower()
        label = "allow" if kind == "@@||" else "block"
        (added if sign == "+" else removed).add((label, domain))
    return added, removed


def fmt(bucket, title):
    if not bucket:
        return []
    allow = sorted(d for k, d in bucket if k == "allow")
    block = sorted(d for k, d in bucket if k == "block")
    out = [f"**{title}: {len(bucket)}** ({len(allow)} allow, {len(block)} block)", ""]
    for label, items in (("allow", allow), ("block", block)):
        if not items:
            continue
        shown = ", ".join(f"`{d}`" for d in items[:SAMPLE])
        more = f" _+{len(items) - SAMPLE} more_" if len(items) > SAMPLE else ""
        out.append(f"- {label}: {shown}{more}")
    out.append("")
    return out


def main():
    diff = sys.stdin.read()
    added, removed = parse(diff)
    if not added and not removed:
        print("No rule changes; CHANGELOG not updated.")
        return 0

    date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    entry = [f"## {date}", ""]
    entry += fmt(added, "Added")
    entry += fmt(removed, "Removed")
    entry_text = "\n".join(entry).rstrip() + "\n\n"

    try:
        with open(CHANGELOG, encoding="utf-8") as fh:
            existing = fh.read()
    except FileNotFoundError:
        existing = HEADER

    # Ensure the insertion marker exists (prepend a header if it's missing).
    if MARKER not in existing:
        existing = HEADER + "\n" + existing

    # New entries always go directly below the marker, newest first.
    head, _, rest = existing.partition(MARKER)
    new = f"{head}{MARKER}\n\n{entry_text}{rest.lstrip(chr(10))}"

    with open(CHANGELOG, "w", encoding="utf-8") as fh:
        fh.write(new)
    print(f"CHANGELOG updated: +{len(added)} / -{len(removed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
