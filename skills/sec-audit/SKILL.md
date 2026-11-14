---
name: sec-audit
description: >
  Read-only intrusion check of a Linux host (computer, VPS, home server) over
  SSH. Takes a dated snapshot of logins, SSH keys, sshd config, listeners, cron/systemd
  persistence, shell startup files, oh-my-zsh origin, packages and file integrity into
  ~/audit_history/, flags red flags, and diffs it against the previous snapshot. Use when
  the user says "check if my server has been compromised", "security audit", "sec audit",
  "intrusion check", "run the audit again", "compare with the last audit", or notices
  something unexplained on a host (unknown software, new shell, odd login). Diagnoses
  only: hardening or cleanup happens only after the user agrees.
allowed-tools: Bash(bash scripts/sec-audit.sh*) Bash(scripts/sec-audit.sh*) Bash(ssh*) Read Write Edit
version: 0.2.0
---

# Security Audit (snapshot + diff)

Good output is a verdict the user can trust: **compromised / not compromised / can't tell**,
the evidence for it, what changed since the last snapshot, and the fixes worth making.
Every check is read-only on the host. Snapshots and host-specific notes stay on the
auditing machine and are never committed.

## Files

| File | Load when |
| --- | --- |
| `scripts/sec-audit.sh` | Always: it runs the audit (`collect`, `diff`, `findings`, `list`, `import`) |
| `scripts/remote-collect.sh` | Only to add or change a check; `sec-audit.sh` pipes it to the host |
| `references/guide.md` | When a finding is WARN/ALERT, the diff shows changes, or the user asks how to use or schedule the audit |
| `references/templates/host-case.md` | When the host has no case yet and the audit came back clean (step 7) |
| `<host dir>/case.md` | Always, if it exists: the host's baseline, known-benign items, accepted risks, audit log |

`<host dir>` is `${SEC_AUDIT_DIR:-~/audit_history}/<user@host>/`. It also holds the snapshots
and `known-benign.txt`.

## Inputs

| Parameter | Source, in order | Example |
| --- | --- | --- |
| `target` | user's message → `SEC_AUDIT_HOST` → ask | `<user>@<host>` |
| `mode` | `quick` if the user asks for a fast check, else full | full ≈ 90 s, quick ≈ 10 s |
| `suspicion` | what made the user worry (e.g. "a tool appeared that I didn't install") | free text |

## Process

1. **Resolve the target** and read `<host dir>/case.md` if it exists. SSH must work
   non-interactively with a key (`ssh -o BatchMode=yes <target> true`). If it doesn't, stop
   and tell the user. Never ask for or type a password.
2. **Collect.** From the skill folder run `bash scripts/sec-audit.sh collect [--quick] <target>`.
   It writes the snapshot, `findings.txt`, and `diff.txt` (vs the previous snapshot), then
   prints a summary. Exit code `2` means at least one ALERT.
3. **Read the results.** Read `findings.txt` and, if present, `diff.txt`. If any line is
   WARN/ALERT or the diff shows changes, load `references/guide.md` and triage each one with
   its section table and false-positive list. Check the case's known-benign items first.
4. **Answer the specific suspicion.** If the user named one, trace its origin with the guide's
   *Tracing an unexplained change* steps: install time, then what else happened then (apt
   history, shell history, the user's own setup scripts).
5. **Dig only where needed.** Use extra read-only SSH commands for open questions. Don't
   change the host in this step.
6. **Report** in the format below. Then offer fixes. Apply a fix only after the user agrees,
   validate it (e.g. `sshd -t`), and re-verify from a new connection.
7. **Record the baseline.** After a clean audit, offer to create or update `<host dir>/case.md`
   from `references/templates/host-case.md` (expected listeners and services, verified benign
   items, audit log row), and to mirror the benign items into `<host dir>/known-benign.txt`.
   Add an entry only for something you verified, with a dated reason.

## Output format

```text
Verdict: <no sign of compromise | compromise indicators found | inconclusive>, one line why.

Suspicion: <what the user asked about> → <origin found, with timestamps and source>

Checks (snapshot <path>):
- <area>: <result>   (one line each; group the OKs)

Changes since <previous snapshot date>: <none | one line per changed section and why>

Recommended fixes (not applied):
1. <highest risk first>

Limits: <what could not be checked, e.g. no sudo, logs rotated before <date>>
```

## Rules

- **Read-only by default.** No installs, no config edits, no restarts, no file deletion on the
  audited host unless the user agreed to that specific fix.
- **Keep host specifics out of this skill.** Usernames, addresses, hostnames, hardware, OS
  versions, installed services and audit history go in `<host dir>/case.md` only, never in
  `SKILL.md`, `references/` or `scripts/`.
- **Never copy secrets into the report, the snapshot or the case.** Point to the file
  ("plaintext tokens in a home-dir file"), never quote its contents. Key material is
  stored as fingerprints only.
- **Don't call something benign by assumption.** Name the evidence (package owner, git
  remote, timestamp, matching apt/shell history).
- If ALERTs suggest a live compromise, follow the guide's *If compromise is likely*
  section: preserve evidence and isolate first. Don't clean up first.

## Chaining

- Changed `scripts/` or `references/` in this repo → `/change-management-1-stage`.
- Regular runs: see `references/guide.md` → *Scheduling*.
