# Contributing to adguard-lists

First off, thank you for your interest in contributing to **adguard-lists**!

This project aims to provide clean, reliable, and well-maintained DNS blocklists and allowlists for AdGuard Home, Technitium DNS Server, and other compatible DNS filtering solutions.

## Ways to Contribute

You can help by:

- Reporting false positives
- Reporting false negatives
- Suggesting new domains to block
- Suggesting domains to whitelist
- Reporting broken websites caused by filtering
- Improving documentation
- Cleaning duplicate or obsolete entries
- Fixing formatting issues

## Before Creating an Issue

Please check that:

- The issue has not already been reported.
- The domain is still active.
- The issue can be reproduced.
- The problem is caused by this repository and not another filter list.

## Reporting False Positives

Please include:

- Website URL
- Blocked domain(s)
- Which list caused the issue
- Description of what is broken
- Screenshots (optional)
- DNS query logs (recommended)

## Reporting False Negatives

Please include:

- Website URL
- Domain(s) that should be blocked
- Reason for blocking (ads, tracking, phishing, malware, etc.)
- Evidence or supporting references if available

## Pull Request Guidelines

Before submitting a Pull Request:

- Test your changes.
- Remove duplicate entries.
- Keep formatting consistent.
- Add one rule per line.
- Do not include unnecessary whitespace.
- Keep comments short and meaningful.
- Verify domains before submitting.
- Avoid adding temporary or short-lived domains.

## Rule Formatting

Examples:

Block a domain:

```
example.com^
```

Allow a domain:

```
@@||example.com^
```

Comment:

```
! Description of rule
```

## Quality Standards

Contributions should:

- Improve filtering accuracy
- Reduce false positives
- Avoid breaking legitimate websites
- Be well researched
- Follow existing formatting

Submissions containing spam, malicious content, intentionally disruptive rules, or low-quality entries may be declined.

## Security Issues

If you discover a security-related issue with this repository, please follow the instructions in the repository's **SECURITY.md** instead of creating a public issue.

## Code of Conduct

Please be respectful and constructive when interacting with other contributors.

## Thank You

Every contribution—whether it's reporting a single false positive or submitting a large pull request—helps improve the quality of these filter lists for everyone.

Thank you for supporting **adguard-lists**!
