# Host case: template

A host case records what the generic guide can't know about one audited host: its
**expected baseline**, the items **verified as benign**, the **risks the owner accepted**,
and an **audit log**.

**Where it lives:** `<SEC_AUDIT_DIR>/<user@host>/case.md`, next to that host's snapshots and
`known-benign.txt`. That is outside any repository, because a case describes one real
machine. **Never commit a filled-in case**, and never put secrets, tokens or file contents in it.

Copy the skeleton below to that path and fill it in after the first clean full audit. For
each section, the questions show what to answer.

---

```markdown
# Host case: <short alias>

## Target
<!-- How to reach it, what it is, what it is for. Who has access? Is sudo passwordless (needed for full coverage)? -->
- Target: `<user>@<host>`; key-only SSH from: <auditing machine>
- OS / role: <distro + release, what services it exists to run>

## Expected baseline (<YYYY-MM-DD>)
<!-- What a clean snapshot looks like. Anything absent from this table that appears in a diff needs an explanation. -->
| Area | Expected |
| --- | --- |
| Accounts | <login accounts and their privileged groups> |
| SSH keys | <number of keys per account and what each belongs to; none for root?> |
| sshd | <hardening drop-in present? password/root login state> |
| Login sources | <known client IPs or subnets> |
| Listeners, all interfaces | <port → process> |
| Listeners, localhost | <port → process> |
| Outbound | <expected long-lived connections, per process> |
| Local units / autostart | <locally added services and timers> |
| Cron | <expected jobs, or "none"> |
| Shell | <shell + framework and its expected origin> |
| Logging | <journald persistent?> |

## Known benign
<!-- Each item that a check flags and you verified as harmless. Mirror each path into known-benign.txt. Re-verify when the owning package changes. -->
| Item | Why it is benign (evidence) | Verified |
| --- | --- | --- |
| <section>: <path or line> | <owning package / git origin / timestamp match> | <YYYY-MM-DD> |

## Accepted risks
<!-- Findings the owner keeps on purpose, and the reason. When should each be re-checked? -->
- <finding>: <reason>

## Audit log
<!-- One row per audit worth remembering: what triggered it, the verdict, fixes applied, open items. Point to files; never quote secrets. -->
| Date | Trigger | Verdict | Notes |
| --- | --- | --- | --- |
| <YYYY-MM-DD> | <routine / suspicion> | <verdict> | <origin found, fixes applied, open items, snapshot id> |
```
