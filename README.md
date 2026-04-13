# Agent Audit Log — Git-Authoritative Path

This directory is the **git-AUTHORITATIVE audit log path** for Claude agents at F&H LLC / Sentinel Aerial.

- SOC2 evidence chain of custody runs through this path, tracked via git history.
- The OneDrive path at `obsidian-dev/agent-office/audit/` is **CONVENIENCE ONLY** (phone access, cross-device skim). It is not authoritative.
- If the two diverge, this path wins. Git history is the tie-breaker.

## Why not OneDrive?

Per CISO ruling (2026-04-13 sign-off, item C): consumer cloud sync under a personal account is not an acceptable sole location for SOC2 evidence. Adam's OneDrive can be wiped, re-synced, or version-rolled without an audit trail. Git cannot.

## Operator note

Recommend running `git init` in this directory to capture append-only history, then pushing to a private remote (e.g., `github.com/irong40/agent-office-audit`). This is an **operator decision** — not auto-initialized by any agent.

Until git is initialized, the filesystem mtime + OneDrive mirror are the fallback evidence chain. Target: git init before 2026-04-17 CISO re-review.

## Schema

Files: `<agent-name>-YYYY-MM.jsonl` — one per agent per month.

**First line of every monthly file MUST be:**

```json
{"ts":"<iso8601>","event":"schema_version","version":"1.0.0","agent":"<agent-name>","canonicalization":"rfc8785","hash_algo":"sha256","hash_truncate":16}
```

This pins the format so readers can detect version drift and future format changes stay diffable.

## arg_hash canonicalization

```
arg_hash = sha256(rfc8785_canonicalize(args_dict)).hexdigest()[:16]
```

- Install: `pip install rfc8785` (standalone, zero deps)
- Canonicalization: RFC 8785 JCS (JSON Canonicalization Scheme) — deterministic across unicode normalization, number formatting, and whitespace.
- Rationale: plain `json.dumps(sort_keys=True)` is ambiguous on float precision (`1` vs `1.0`), unicode escapes, and non-ASCII characters. RFC 8785 pins all three.

## Append-only rule

Agents MUST NOT edit, reorder, or delete prior lines. Integrity is enforced by:
- Agent SKILL.md rules (file-append mode only)
- Git history (this path)
- Future: git hook rejecting non-append diffs

## Current agents writing here

- `email-processor` (primary write; OneDrive mirror for convenience)
