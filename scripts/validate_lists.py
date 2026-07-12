#!/usr/bin/env python3
"""
validate_lists.py — Validate AdGuard Home block/allow lists.

Checks performed:
  1. Syntax     — every non-comment line is a well-formed rule (||domain^ or @@||domain^).
  2. Duplicates — the same domain listed more than once, within a file or across files.
  3. DNS (live) — each unique domain is queried to see whether it still resolves.

Exit codes:
  0  everything passed (DNS misses are warnings by default)
  1  syntax errors or duplicates were found
  2  DNS failures were found AND --strict-dns was given

Usage:
  python validate_lists.py                         # syntax + duplicate checks on every *.txt (fast)
  python validate_lists.py file1.txt file2.txt     # checks only the files you name
  python validate_lists.py --dns paswhitelist.txt  # also live-check DNS (opt-in; use on small lists)
  python validate_lists.py --strict-dns file.txt   # treat unresolved domains as failures
"""

import argparse
import glob
import os
import re
import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


def discover_lists():
    """Find every *.txt file in the repo (recursive), excluding .git."""
    found = []
    for path in glob.glob("**/*.txt", recursive=True):
        if ".git" + os.sep in path or path.startswith(".git" + os.sep):
            continue
        found.append(path)
    return sorted(found)

# Matches an AdGuard network rule and captures the domain.
#   optional @@ (allow), then ||, the domain, then ^, then optional modifiers ($...)
RULE_RE = re.compile(r"^(@@)?\|\|([A-Za-z0-9_.*-]+)\^(\$[^\s]*)?$")

# Sanity check for the captured domain. Accepts normal domains, a leading
# "*." wildcard, underscores (e.g. _dmarc), and punycode/IDN TLDs (xn--...).
DOMAIN_RE = re.compile(
    r"^(\*\.)?([A-Za-z0-9_-]+\.)+(?:[A-Za-z]{2,}|xn--[A-Za-z0-9-]+)$"
)

# Adblock/AdGuard regex rules are wrapped in /slashes/, optionally with a
# leading @@ (allow) and trailing $modifiers. These are valid, not malformed.
REGEX_RULE_RE = re.compile(r"^(@@)?/.+/(\$[^\s]*)?$")


def parse_file(path):
    """Return (rules, errors, warnings).

    errors   = hard problems (malformed rules) -> fail the run.
    warnings = soft problems (odd-looking domains) -> reported only.
    rules    = list of (domain, is_allow, lineno).
    """
    rules = []
    errors = []
    warnings = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except FileNotFoundError:
        errors.append((0, f"file not found: {path}"))
        return rules, errors, warnings

    for i, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("!") or line.startswith("#"):
            continue  # comment or blank
        if line.startswith("[") and line.endswith("]"):
            continue  # list-format header, e.g. [Adblock Plus 2.0]
        m = RULE_RE.match(line)
        if not m:
            if REGEX_RULE_RE.match(line):
                continue  # valid regex rule (/.../ or @@/.../), not a domain
            errors.append((i, f"malformed rule: {line!r}"))
            continue
        domain = m.group(2).lower()
        is_allow = m.group(1) == "@@"
        if "*" not in domain and not DOMAIN_RE.match(domain):
            # Unusual but not necessarily wrong (odd TLDs, IDN, etc.) — warn only.
            warnings.append((i, f"unusual domain: {domain!r}"))
        rules.append((domain, is_allow, i))
    return rules, errors, warnings


def resolve(domain):
    """Return True if the domain resolves (A/AAAA), False otherwise."""
    if "*" in domain:
        return True  # wildcards can't be resolved directly; skip
    try:
        socket.getaddrinfo(domain, None)
        return True
    except socket.gaierror:
        return False
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description="Validate AdGuard Home lists.")
    ap.add_argument("files", nargs="*",
                    help="list files to validate (default: auto-discover every *.txt in the repo)")
    ap.add_argument("--dns", action="store_true",
                    help="run a live DNS check (opt-in; slow on large lists)")
    ap.add_argument("--strict-dns", action="store_true",
                    help="implies --dns and fails the run when a domain does not resolve")
    ap.add_argument("--workers", type=int, default=32, help="parallel DNS lookups")
    args = ap.parse_args()
    do_dns = args.dns or args.strict_dns

    files = args.files or discover_lists()
    if not files:
        print("No .txt list files found to validate.")
        return 1
    syntax_errors = 0
    warn_count = 0
    all_rules = []          # (domain, is_allow, file, lineno)
    seen = {}               # domain -> list of "file:line"
    per_file = {}           # file -> {domain -> [line numbers]}

    print("=" * 60)
    print("AdGuard list validation")
    print("=" * 60)

    for path in files:
        rules, errors, warnings = parse_file(path)
        print(f"\n[{path}]  {len(rules)} rules, {len(errors)} error(s), {len(warnings)} warning(s)")
        for ln, msg in errors:
            print(f"  ✗ line {ln}: {msg}")
            syntax_errors += 1
        for ln, msg in warnings[:10]:
            print(f"  ⚠ line {ln}: {msg}")
        if len(warnings) > 10:
            print(f"  ⚠ ...and {len(warnings) - 10} more warnings")
        warn_count += len(warnings)
        for domain, is_allow, ln in rules:
            all_rules.append((domain, is_allow, path, ln))
            seen.setdefault(domain, []).append(f"{path}:{ln}")
            per_file.setdefault(path, {}).setdefault(domain, []).append(ln)

    # ---- duplicates ----
    # Within-file duplicates are genuine redundancy -> failure.
    # Cross-file overlaps are informational (e.g. a domain in both an
    # allow list and a block list) -> warning only.
    within_dupes = 0
    print("\n[duplicates: within a file]")
    for path, domains in per_file.items():
        for d, lns in sorted(domains.items()):
            if len(lns) > 1:
                print(f"  ✗ {path}: {d} on lines {', '.join(map(str, lns))}")
                within_dupes += 1
    if within_dupes == 0:
        print("  none ✓")

    cross_dupes = {d: locs for d, locs in seen.items()
                   if len({loc.rsplit(':', 1)[0] for loc in locs}) > 1}
    print(f"\n[duplicates: across files]  {len(cross_dupes)} domain(s) in more than one file (info only)")
    for d, locs in sorted(cross_dupes.items()):
        print(f"  ⚠ {d}  ->  {', '.join(locs)}")

    # ---- DNS ----
    dns_failures = []
    if do_dns:
        unique = sorted({d for d, *_ in all_rules if "*" not in d})
        print(f"\n[dns]  resolving {len(unique)} unique domain(s)...")
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(resolve, d): d for d in unique}
            for fut in as_completed(futs):
                d = futs[fut]
                if not fut.result():
                    dns_failures.append(d)
        if dns_failures:
            print(f"  {len(dns_failures)} domain(s) did NOT resolve:")
            for d in sorted(dns_failures):
                print(f"  ✗ {d}  ({', '.join(seen[d])})")
        else:
            print("  all domains resolved ✓")
    else:
        print("\n[dns]  skipped (pass --dns to enable)")

    # ---- summary + exit code ----
    print("\n" + "=" * 60)
    print(f"Summary: {syntax_errors} error(s), "
          f"{within_dupes} within-file duplicate(s), "
          f"{warn_count} warning(s), "
          f"{len(cross_dupes)} cross-file overlap(s), "
          f"{len(dns_failures)} unresolved domain(s)")
    print("=" * 60)

    if syntax_errors or within_dupes:
        return 1
    if dns_failures and args.strict_dns:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
