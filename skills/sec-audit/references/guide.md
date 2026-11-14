# sec-audit guide

For humans running the audit by hand and for AI agents triaging its output. Part 1 covers
running it. Part 2 covers reading the results. Part 3 covers acting on them.

Paths below are relative to the skill folder (`sec-audit/`).

---

## Part 1 — Running it

### Requirements

| Where | Needs |
| --- | --- |
| Auditing machine (macOS/Linux) | bash 3.2+, `ssh` with a key loaded in the agent, `diff`, `awk` |
| Audited host (Debian-family Linux) | bash, `ss`, `systemctl`, `journalctl`, `dpkg`. **Passwordless sudo** for full coverage: without it, root-only checks (shadow, other users' crontabs, `sshd -T`, process owners, integrity) are partial and `findings.txt` says so |

### Commands

```bash
cd <skills-dir>/sec-audit

scripts/sec-audit.sh collect user@host          # full (~90 s): + setuid scan + dpkg -V
scripts/sec-audit.sh collect --quick user@host  # quick (~10 s): skips the two slow checks
scripts/sec-audit.sh list user@host             # history: ALERT/WARN counts + what changed
scripts/sec-audit.sh diff user@host             # latest two snapshots
scripts/sec-audit.sh diff user@host <OLD_SNAPSHOT> <NEW_SNAPSHOT>
scripts/sec-audit.sh findings ~/audit_history/user@host/<NEW_SNAPSHOT>
```

Set `SEC_AUDIT_HOST=user@host` to omit the target. Set `SEC_AUDIT_DIR` to keep
snapshots somewhere else (default `~/audit_history`).

**Without SSH from the auditing machine** (e.g. you only have the console): copy
`scripts/remote-collect.sh` to the host, run `bash remote-collect.sh > raw.txt`, bring
`raw.txt` back, then run `scripts/sec-audit.sh import user@host raw.txt`.

### Snapshot layout

```text
~/audit_history/                       (chmod 700)
└── user@host/
    ├── case.md                        # host baseline + audit log (from references/templates/host-case.md)
    ├── known-benign.txt               # per-host allowlist (optional, you maintain it)
    ├── YYYY-MM-DD_HHMMSS/
    │   ├── raw.txt                    # full collector output
    │   ├── stderr.txt                 # collector errors (should be empty)
    │   ├── sections/<name>.txt        # one file per check, the unit of comparison
    │   ├── findings.txt               # ALERT / WARN / INFO / OK lines
    │   └── diff.txt                   # vs the previous snapshot (absent on the first)
    └── YYYY-MM-DD_HHMMSS/ ...
```

Snapshots are plain text, so `diff -r`, `grep -r` and editors all work on them. Everything
under `~/audit_history/` describes a real machine, so keep it out of any repository.

### Scheduling

Audit weekly, and also after any install session or anything else unexplained. Use a full
run weekly and quick runs in between. Your SSH key must be usable without a prompt from the
scheduler: an agent key loaded at login, or a dedicated key restricted on the host side.

**macOS (launchd)**: `~/Library/LaunchAgents/local.sec-audit.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>local.sec-audit</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string><string>-lc</string>
    <string>&lt;skills-dir&gt;/sec-audit/scripts/sec-audit.sh collect user@host &gt;&gt; ~/audit_history/cron.log 2&gt;&amp;1</string>
  </array>
  <key>StartCalendarInterval</key><dict><key>Weekday</key><integer>0</integer><key>Hour</key><integer>9</integer></dict>
</dict></plist>
```

Load it with `launchctl load ~/Library/LaunchAgents/local.sec-audit.plist`.

**Linux (cron)**: `0 9 * * 0 <skills-dir>/sec-audit/scripts/sec-audit.sh collect user@host >> ~/audit_history/cron.log 2>&1`

Exit code `2` means an ALERT, so you can wire it to a notification.

**Retention**: a snapshot is about 300 KB. Prune old ones by hand, or with
`ls -d ~/audit_history/*/20* | head -n -52 | xargs rm -r` on GNU systems. Keep the first
snapshot as the original baseline.

---

## Part 2 — Reading the results

### Severity

| Level | Meaning | Action |
| --- | --- | --- |
| **ALERT** | A strong compromise indicator or a dangerous setting | Stop and investigate now. Read *If compromise is likely* first |
| **WARN** | Abnormal or risky, often with a benign explanation | Triage with the section table and the false-positive list |
| **INFO** | Context: exposure, NOPASSWD sudo, login sources, skipped checks | Review once, then note it in the host's `case.md` |
| **OK** | Check passed | — |

### Sections

*Stable* sections are compared run to run. *Volatile* ones are kept for reading but never
diffed.

| Section | What it holds | Diffed | Red flag | Usually benign |
| --- | --- | --- | --- | --- |
| `meta` | time, kernel, OS, uptime, sudo available | no | `sudo=no` (partial audit) | — |
| `users` | real accounts, uid 0 list, sudo/adm/docker groups, empty passwords | yes | new account, extra uid 0, new sudo/docker member, empty password | account added by a package you installed (check `apt_history`) |
| `sudoers` | effective sudo rules | yes | new rule, especially `NOPASSWD` for an unexpected user | distro defaults |
| `ssh_keys` | fingerprint of each authorized key, all users and root | yes | **any key you don't recognise** | — |
| `sshd` | effective sshd settings + drop-in list | yes | password auth back on, root login enabled, new drop-in | your own hardening |
| `auth_sources` | unique (result, method, user, source IP), 30 days | yes | accepted login from an unknown IP or with an unexpected method | new laptop or phone on your LAN |
| `auth_counts` / `logins` / `failed_logins` | counts, `last`, `lastb` | no | invalid-user bursts (brute force), logins at odd hours | — |
| `listeners` | listening sockets with process name | yes | new port, especially on `0.0.0.0`/`[::]`/`*`, or an odd process name | new service you installed |
| `connections` | established peers per process | no | long-lived connection to an unknown IP from a shell, `python`, `nc`, `perl` | browsers, chat-bot or agent gateways calling their API, package mirrors |
| `network` | interfaces, routes, resolv.conf, hosts | yes | changed DNS server, new hosts entries redirecting known domains | DHCP lease changes, docker networks |
| `firewall` | iptables/nft rules (no counters) | yes | new ACCEPT for an inbound port, rules flushed | docker restarting containers |
| `cron`, `timers` | all crontabs, cron dirs, at jobs, systemd timers | yes | **any new job you didn't create**, especially one that downloads (`curl`/`wget`) | package-installed timers |
| `services`, `unit_files` | enabled/running services; hashes of local unit and autostart files | yes | new enabled service, changed unit hash, autostart entry | services you installed |
| `persistence` | `ld.so.preload`, ssh `rc`/`environment`, hashes of shell startup files | yes | anything in `ld.so.preload` (**ALERT**), new `~/.ssh/rc`, changed rc hash you didn't edit | you edited your `.zshrc` |
| `rc_suspicious` | startup-file lines with curl/wget/base64/`/dev/tcp`/nc/`eval $(…)` | yes | download-and-execute or reverse-shell lines | tool installers adding `eval "$(tool init)"` |
| `kernel_modules` | loaded modules | yes | unknown module, especially after no kernel update | new hardware, docker (`br_netfilter`, `overlay`) |
| `omz` | per install: origin, branch, install time, modified files, custom files | yes | origin not `github.com/ohmyzsh/ohmyzsh` (**ALERT**), modified files, unexpected custom plugins | your own themes/plugins in `custom/` |
| `packages`, `apt_history` | package list; last 50 apt commands with requester | yes | installs nobody remembers, especially `Requested-By` missing (root/cron) | `apt-daily-upgrade` upgrades |
| `docker` | containers and images | yes | unknown container or image (cryptominers like to hide here) | your own stacks |
| `processes` | unique user + command (no kernel threads, no collector) | yes | new daemon, shell running as a service user | new desktop session, per-client child of a file-sharing daemon |
| `suspicious_procs` | processes running a deleted or temp-dir binary | no | binary in `/tmp`, `/dev/shm`, or deleted and not package-owned | daemon still running an old binary after an upgrade |
| `tmp_files` | executables and hidden entries in `/tmp`, `/var/tmp`, `/dev/shm` | yes | any executable, hidden dirs like `/tmp/.x` | build caches |
| `recent_changes` | system files changed in the last 7 days | no | `/usr/bin` changes without a matching apt run | upgrades |
| `logging` | journald storage | yes | storage switched off persistent | — |
| `suid` *(full)* | setuid/setgid files | yes | new setuid file, especially outside `/usr/bin` and `/usr/lib` | new package ships one |
| `integrity` *(full)* | package files failing `dpkg -V` (conffiles excluded) | yes | changed binary/library under `/usr` (**likely rootkit**) | distro packaging tweaks; verify, then add to `known-benign.txt` |

### Reading a diff

`diff.txt` starts with `# changed: <sections>`, then a unified diff per section (`+` new,
`-` gone). For each changed section:

1. Ask: does the user, or `apt_history`, explain it at that time?
2. A `+` line in `ssh_keys`, `cron`, `timers`, `unit_files`, `sudoers`, `persistence`,
   `suid` or `integrity` needs an explanation before you call the audit clean.
3. A diff between a full and a `--quick` snapshot skips `suid` and `integrity`. Diff two
   full snapshots for those.

### False positives seen in practice

| Signal | Benign cause | How to confirm |
| --- | --- | --- |
| `~/.oh-my-zsh` modified today | oh-my-zsh auto-update on shell start | `git -C ~/.oh-my-zsh log -3` shows upstream commits; `git status` is clean; origin is official |
| `integrity`: a non-binary package file (browser defaults, distribution config) | some distros and OS images ship package files already modified by their own packaging | `dpkg -S <file>` names a distro customisation package; mtime equals the OS install date; content is stock defaults. Never apply this to binaries or libraries under `/usr` |
| `suspicious_procs` "(deleted)" | daemon not restarted after an upgrade | `dpkg -S` on the path without " (deleted)"; `apt_history` shows the upgrade; restart clears it |
| `rc_suspicious` `eval "$(tool init)"` | normal tool setup (dircolors, ssh-agent, brew, pyenv, zoxide) | the tool is installed and you set it up |
| `processes`: a daemon's name under a login user | file-sharing or remote-access daemons fork a child per connected client, running as that user | a matching client connection appears in `connections` |
| `listeners` new 127.0.0.1 port | local-only service (LLM server, dashboard) | process name matches something you run; not exposed |

---

## Part 3 — Acting on it

### Tracing an unexplained change

When the user says "X appeared and I don't know why":

1. **Birth time**: `stat <path>` (`Birth:`). `Modify:` alone is misleading because updates
   touch it.
2. **What else happened at that moment**:
   `find ~ -maxdepth 2 -newermt "<birth - 1h>" ! -newermt "<birth + 1h>"`,
   `/var/log/apt/history.log*` (`Commandline` + `Requested-By`), and the shell histories
   (`~/.bash_history`, `~/.zsh_history`: the first entries after the switch date).
3. **Who ran it**: `Requested-By` in apt history, `last` around the time, sudo entries in the
   journal (only if logs were persistent then).
4. **Is it in the user's own tooling?**
   `grep -rIn "<name or installer URL>" ~/git ~/bin ~/scripts`. Provisioning scripts and
   dotfile frameworks are the most common answer.
5. **Is the artifact genuine?** For a git checkout: `remote -v`, `status`, and recent log
   authors. For a package: `dpkg -S` + `dpkg -V`. For a binary: its owning package.

Typical shape of a benign answer: the artifact's birth time sits inside a burst of installs
(e.g. `apt install zsh`, then the framework a minute later, then other tooling). Every
`Requested-By` is the owner, the owner's own setup scripts contain the official installer
call, and the checkout is clean on the official origin. Verdict: installed by the owner's
tooling, not an intruder. Without such a chain, or if `Requested-By` is missing or is an
unexpected account, keep digging.

### If compromise is likely

1. **Don't reboot and don't clean up yet.** Volatile evidence (processes, connections,
   `/dev/shm`) disappears.
2. **Preserve**: run a full `collect` now (it is the evidence copy). Also copy
   `/var/log/journal`, `/var/log/auth.log*` and suspect binaries off the host.
3. **Isolate**: unplug the host from the network, or block it at the router. Change
   passwords and revoke tokens **from another machine**, because the host's own keys,
   tokens and `.env` files must be considered stolen.
4. **Rebuild, don't repair**: a rooted host (integrity failures in `/usr`, `ld.so.preload`,
   unknown setuid files) gets a clean reinstall from known-good media. Then restore data,
   never binaries or dotfiles, from the compromised system.
5. Rotate every credential the host held: SSH keys it stored, API/bot tokens, and cloud
   credentials.

### Common fixes (apply only with the user's agreement)

| Finding | Fix | Verify |
| --- | --- | --- |
| `sshd.password` / `sshd.root` | drop-in `/etc/ssh/sshd_config.d/00-hardening.conf`: `PasswordAuthentication no`, `KbdInteractiveAuthentication no`, `PermitRootLogin no`. The first value wins in sshd, so the file name must sort first | `sshd -t`, `systemctl reload ssh`, `sshd -T`, new key login works, `ssh -o PubkeyAuthentication=no` is refused |
| `logging` not persistent | drop-in `/etc/systemd/journald.conf.d/50-persistent.conf`: `[Journal]`, `Storage=persistent`, `SystemMaxUse=500M`; then `systemctl restart systemd-journald` | `journalctl --header \| grep 'File path'` under `/var/log/journal` |
| `sudo.nopasswd` | Remove the `NOPASSWD` rule, or limit it to specific commands. Weigh this against unattended jobs that need it: the audit itself does | `sudo -n true` fails as expected |
| `exposure` of file-sharing / remote-desktop ports | bind them to the LAN interface or firewall them; never port-forward them | `ss -tulpn` |
| plaintext secrets in home | move to a password manager or a `chmod 600` env file; rotate anything that was world-readable | `ls -l` |

After a fix, run `collect --quick` again. The diff should show only the intended change.

---

## Extending the checks (maintainers)

- Add a section to `scripts/remote-collect.sh` with `sec <name>`. It must stay **read-only**
  and be **deterministic**: sorted, with no PIDs, counters or timestamps. If it can't be,
  add its name to `VOLATILE_SECTIONS` in `scripts/sec-audit.sh`.
- Never collect secret material. Store fingerprints and hashes, not contents.
- Add a red-flag check in `run_findings` (`emit LEVEL check.name "detail"`) and a test case
  in `scripts/test_sec_audit.py`. Run `python3 scripts/test_sec_audit.py`.
- Add the section to the table above.
