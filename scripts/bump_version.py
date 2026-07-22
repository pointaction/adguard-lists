#!/usr/bin/env python3
"""Bump '! Version:' (+0.1) and set '! Last modified:' to today (UTC) for list files."""
import re
import sys
from datetime import datetime, timezone

VERSION_RE = re.compile(r'^(!\s*Version:\s*)(\d+(?:\.\d+)?)\s*$', re.IGNORECASE)
MODIFIED_RE = re.compile(r'^(!\s*Last modified:\s*).*$', re.IGNORECASE)

def bump(value):
    return f"{round(float(value) + 0.1, 1):.1f}"

def process(path, today):
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    version_idx = None
    modified_done = False
    for i, line in enumerate(lines):
        m = VERSION_RE.match(line)
        if m and version_idx is None:
            lines[i] = m.group(1) + bump(m.group(2)) + "\n"
            version_idx = i
            continue
        if MODIFIED_RE.match(line) and not modified_done:
            lines[i] = "! Last modified: " + today + "\n"
            modified_done = True
    if version_idx is None:
        print(f"  no Version header in {path}; skipped")
        return False
    if not modified_done:
        lines.insert(version_idx + 1, "! Last modified: " + today + "\n")
    with open(path, "w", encoding="utf-8") as fh:
        fh.writelines(lines)
    print(f"  bumped {path}")
    return True

def main(argv):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for path in argv:
        try:
            process(path, today)
        except FileNotFoundError:
            print(f"  {path} not found; skipped")

if __name__ == "__main__":
    main(sys.argv[1:])
