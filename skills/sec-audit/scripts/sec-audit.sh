#!/usr/bin/env bash
# sec-audit.sh — snapshot a Linux host's intrusion-diagnostic state over SSH, flag red
# flags, and diff the snapshot against the previous one.
#
# Runs on the auditing machine (bash 3.2+, macOS or Linux). The collection itself is
# remote-collect.sh, piped to the host over SSH; it is read-only on the host.
#
# Usage:
#   sec-audit.sh collect [--quick] [user@host]   take a snapshot, then write findings + diff
#   sec-audit.sh diff [user@host] [OLD] [NEW]    diff two snapshots (default: the latest two)
#   sec-audit.sh findings SNAPSHOT_DIR           re-run the red-flag checks on a snapshot
#   sec-audit.sh list [user@host]                list snapshots and their finding counts
#   sec-audit.sh import user@host RAW_FILE       turn a saved collector output into a snapshot
#                                                (e.g. remote-collect.sh run by hand on the host)
#
# Environment:
#   SEC_AUDIT_DIR    where snapshots go        (default: ~/audit_history)
#   SEC_AUDIT_HOST   default user@host target  (no default)
#   SEC_AUDIT_TS     override the snapshot timestamp (tests)
#
# Layout:  $SEC_AUDIT_DIR/<user@host>/<YYYY-MM-DD_HHMMSS>/
#            raw.txt  stderr.txt  sections/<name>.txt  findings.txt  diff.txt
#
# Exit codes: 0 ok, 1 usage/collection error, 2 snapshot has ALERT findings.

set -eu
export LC_ALL=C

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUDIT_DIR="${SEC_AUDIT_DIR:-$HOME/audit_history}"
# Sections that change on every run; kept in the snapshot but left out of the diff.
VOLATILE_SECTIONS="meta auth_counts logins failed_logins connections suspicious_procs recent_changes"

die()   { echo "sec-audit: $*" >&2; exit 1; }
usage() { sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }

label_of()  { printf '%s' "$1" | tr -c 'A-Za-z0-9@._-' '_'; }
host_dir()  { echo "$AUDIT_DIR/$(label_of "$1")"; }
snapshots() { [ -d "$1" ] && ls -1 "$1" | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{6}$' | sort || true; }
is_volatile() { case " $VOLATILE_SECTIONS " in *" $1 "*) return 0;; esac; return 1; }

resolve_target() {
  local t="${1:-${SEC_AUDIT_HOST:-}}"
  [ -n "$t" ] || die "no target: pass user@host or set SEC_AUDIT_HOST"
  echo "$t"
}

# ---------------------------------------------------------------- split
split_raw() { # snapdir
  local snap="$1"
  mkdir -p "$snap/sections"
  awk -v dir="$snap/sections" '
    /^=====SECTION [A-Za-z0-9_]+=====$/ {
      if (out != "") close(out)
      name = $0; sub(/^=====SECTION /, "", name); sub(/=====$/, "", name)
      out = dir "/" name ".txt"; printf "" > out; next }
    out != "" && $0 != "" { print > out }' "$snap/raw.txt"
}

# ---------------------------------------------------------------- findings
sect() { cat "$1/sections/$2.txt" 2>/dev/null || true; }
has()  { [ -f "$1/sections/$2.txt" ]; }
# Lines of a section that are not marked known-benign. The allowlist is
# <host dir>/known-benign.txt: one fixed string per line (# comments allowed); a section
# line containing any of them is suppressed. Applies to rc_suspicious, tmp_files,
# suspicious_procs and integrity only.
SUPPRESSED=0
flagged() { # snapdir section
  local kb all kept
  kb="$(dirname "$1")/known-benign.txt"
  all=$(sect "$1" "$2" | grep -v '^#' || true)
  if [ -s "$kb" ] && grep -qvE '^[[:space:]]*(#|$)' "$kb"; then
    kept=$(printf '%s\n' "$all" | grep -vFf <(grep -vE '^[[:space:]]*(#|$)' "$kb") || true)
  else
    kept="$all"
  fi
  SUPPRESSED=$(( SUPPRESSED + $(printf '%s\n' "$all" | grep -c . || true) - $(printf '%s\n' "$kept" | grep -c . || true) ))
  printf '%s\n' "$kept" | grep . || true
}
count() { grep -c . || true; }
emit() { printf '%-5s %-22s %s\n' "$1" "$2" "$3"; }

run_findings() { # snapdir
  local s="$1" v n
  [ -d "$s/sections" ] || die "not a snapshot: $s"

  v=$(sect "$s" meta | sed -n 's/^sudo=//p')
  [ "$v" = "yes" ] && emit OK collection "ran with sudo" || emit WARN collection "no passwordless sudo: root-only checks are incomplete"
  [ -s "$s/stderr.txt" ] && emit INFO collection "collector wrote to stderr: see stderr.txt"

  # SSH daemon
  v=$(sect "$s" sshd | awk '$1=="passwordauthentication"{print $2}')
  case "$v" in no) emit OK sshd.password "password auth disabled";; "") emit WARN sshd.password "unknown (sshd -T unavailable)";; *) emit WARN sshd.password "password auth enabled";; esac
  v=$(sect "$s" sshd | awk '$1=="permitrootlogin"{print $2}')
  case "$v" in no) emit OK sshd.root "root login disabled";; yes) emit ALERT sshd.root "root login with password allowed";; "") emit WARN sshd.root "unknown";; *) emit WARN sshd.root "root login allowed ($v)";; esac
  v=$(sect "$s" sshd | awk '$1=="permitemptypasswords"{print $2}')
  [ "$v" = "yes" ] && emit ALERT sshd.empty "empty passwords permitted"

  # Accounts
  v=$(sect "$s" users | sed -n 's/^# uid0: //p' | tr -s ' ' | sed 's/ *$//')
  if [ -n "$v" ] && [ "$v" != "root" ]; then emit ALERT users.uid0 "extra uid 0 accounts: $v"; else emit OK users.uid0 "only root has uid 0"; fi
  v=$(sect "$s" users | sed -n '/^# empty-password accounts:/,$p' | sed 1d | tr '\n' ' ')
  [ -n "$v" ] && emit ALERT users.nopass "accounts with empty password: $v"
  sect "$s" sudoers | grep -q NOPASSWD && emit INFO sudo.nopasswd "NOPASSWD sudo rule present: $(sect "$s" sudoers | grep NOPASSWD | tr '\n' ';')"

  # Persistence and tampering
  v=$(sect "$s" persistence | sed -n '/^# \/etc\/ld.so.preload/{n;p;}')
  if [ -n "$v" ] && [ "$v" != "(none)" ] && [ "${v#\#}" = "$v" ]; then emit ALERT ld.so.preload "preload set: $v"; else emit OK ld.so.preload "not set"; fi
  # $(...) runs in a subshell, so SUPPRESSED is tallied from a second call into a temp var.
  SUPPRESSED=0
  for sec_name in rc_suspicious tmp_files suspicious_procs integrity; do flagged "$s" "$sec_name" >/dev/null; done
  n=$(flagged "$s" rc_suspicious | count)
  if [ "$n" -gt 0 ]; then emit WARN shell.rc "$n suspicious line(s) in shell startup files: see sections/rc_suspicious.txt"; else emit OK shell.rc "no download/decode/socket lines in shell startup files"; fi
  n=$(flagged "$s" tmp_files | count)
  if [ "$n" -gt 0 ]; then emit WARN tmp.files "$n executable/hidden file(s) in temp dirs: see sections/tmp_files.txt"; else emit OK tmp.files "nothing executable or hidden in /tmp, /var/tmp, /dev/shm"; fi
  n=$(flagged "$s" suspicious_procs | count)
  if [ "$n" -gt 0 ]; then emit WARN procs "$n process(es) running a deleted or temp-dir binary: see sections/suspicious_procs.txt"; else emit OK procs "no process runs from a deleted or temp binary"; fi
  if has "$s" integrity; then
    n=$(flagged "$s" integrity | count)
    if [ "$n" -gt 0 ]; then emit WARN integrity "$n package file(s) differ from dpkg checksums: see sections/integrity.txt"; else emit OK integrity "all package files match dpkg checksums"; fi
  else
    emit INFO integrity "skipped (--quick)"
  fi
  [ "$SUPPRESSED" -gt 0 ] && emit INFO known-benign "$SUPPRESSED line(s) suppressed by $(dirname "$s")/known-benign.txt"

  # oh-my-zsh
  if sect "$s" omz | grep -q '^(no oh-my-zsh'; then
    emit INFO omz "not installed"
  else
    sect "$s" omz | awk '
      /^# /         { d=$2 }
      /^remote=/    { r=substr($0,8); if (r !~ /github\.com[:\/]ohmyzsh\/ohmyzsh(\.git)?$/) printf "ALERT|omz.remote|%s origin is %s\n", d, (r==""?"(none)":r) }
      /^dirty_files:/ { m="dirty"; next }
      /^custom_files:/ { m="custom"; next }
      /^  / && m=="dirty"  { nd[d]++ }
      /^  / && m=="custom" { nc[d]++ }
      /^[a-z]+=/ { m="" }
      END { for (k in nd) printf "WARN|omz.dirty|%s has %d locally modified file(s): see sections/omz.txt\n", k, nd[k]
            for (k in nc) printf "INFO|omz.custom|%s has %d custom file(s): review sections/omz.txt\n", k, nc[k] }' \
    | while IFS='|' read -r a b c; do emit "$a" "$b" "$c"; done
    sect "$s" omz | grep -E '^remote=' | grep -qvE 'github\.com[:/]ohmyzsh/ohmyzsh(\.git)?$' || emit OK omz.remote "origin is the official ohmyzsh repo"
  fi

  # Logins
  n=$(sect "$s" auth_counts | sed -n 's/^invalid_user_30d=//p'); n=${n:-0}
  [ "$n" -gt 0 ] && emit WARN ssh.bruteforce "$n invalid-user attempts in 30 days"
  n=$(sect "$s" auth_counts | sed -n 's/^failed_30d=//p'); n=${n:-0}
  [ "$n" -gt 0 ] && emit INFO ssh.failed "$n failed logins in 30 days"
  v=$(sect "$s" auth_sources | awk '$1=="accepted"{print $4}' | sort -u | tr '\n' ' ')
  [ -n "$v" ] && emit INFO ssh.sources "accepted logins from: $v"

  # Exposure and logging
  v=$(sect "$s" listeners | awk '$2 ~ /^(0\.0\.0\.0|\*|\[::\]):/ {split($2,a,":"); p=a[length(a)]; print $1"/"p}' | sort -u | tr '\n' ' ')
  [ -n "$v" ] && emit INFO exposure "listening on all interfaces: $v"
  v=$(sect "$s" logging | sed -n 's/^persistent_dir=//p')
  [ "$v" = "yes" ] && emit OK logging "journal is persistent" || emit WARN logging "journal is not persistent: history is lost on reboot"
}

# ---------------------------------------------------------------- diff
run_diff() { # old new
  local old="$1" new="$2" name changed="" f
  for f in $( (ls -1 "$old/sections" "$new/sections" 2>/dev/null) | grep '\.txt$' | sort -u); do
    name="${f%.txt}"
    is_volatile "$name" && continue
    if ! cmp -s "$old/sections/$f" "$new/sections/$f" 2>/dev/null; then
      if [ -f "$old/sections/$f" ] && [ -f "$new/sections/$f" ]; then changed="$changed $name"; fi
    fi
  done
  echo "# sec-audit diff"
  echo "# old: $old"
  echo "# new: $new"
  echo "# volatile sections not compared: $VOLATILE_SECTIONS"
  if [ -z "$changed" ]; then
    echo "# result: no change in stable sections"
    return 0
  fi
  echo "# changed:$changed"
  for name in $changed; do
    echo
    echo "## $name"
    diff -u "$old/sections/$name.txt" "$new/sections/$name.txt" | sed '1,2d' || true
  done
}

summarize() { # snapdir
  local s="$1"
  echo "snapshot: $s"
  printf 'findings: %s ALERT, %s WARN, %s INFO, %s OK\n' \
    "$(grep -c '^ALERT' "$s/findings.txt" || true)" "$(grep -c '^WARN' "$s/findings.txt" || true)" \
    "$(grep -c '^INFO' "$s/findings.txt" || true)"  "$(grep -c '^OK' "$s/findings.txt" || true)"
  grep -E '^(ALERT|WARN)' "$s/findings.txt" | sed 's/^/  /' || true
  if [ -f "$s/diff.txt" ]; then
    echo "diff: $(grep -E '^# (result|changed):' "$s/diff.txt" | sed 's/^# //')"
  else
    echo "diff: first snapshot for this host, nothing to compare"
  fi
}

finish_snapshot() { # target snapdir
  local hd prev
  split_raw "$2"
  run_findings "$2" > "$2/findings.txt"
  hd=$(host_dir "$1")
  prev=$(snapshots "$hd" | grep -v "^$(basename "$2")$" | tail -1)
  [ -n "$prev" ] && run_diff "$hd/$prev" "$2" > "$2/diff.txt"
  summarize "$2"
  grep -q '^ALERT' "$2/findings.txt" && return 2 || return 0
}

new_snapdir() { # target
  local d
  d="$(host_dir "$1")/${SEC_AUDIT_TS:-$(date +%Y-%m-%d_%H%M%S)}"
  [ -e "$d" ] && die "snapshot already exists: $d"
  mkdir -p "$d"; chmod 700 "$AUDIT_DIR" 2>/dev/null || true
  echo "$d"
}

# ---------------------------------------------------------------- commands
cmd="${1:-}"; [ $# -gt 0 ] && shift
case "$cmd" in
  collect)
    quick=""
    [ "${1:-}" = "--quick" ] && { quick="--quick"; shift; }
    target=$(resolve_target "${1:-}")
    snap=$(new_snapdir "$target")
    echo "collecting from $target ${quick:+(quick)}..." >&2
    if ! ssh -o BatchMode=yes -o ConnectTimeout=15 "$target" "bash -s -- $quick" \
         < "$SCRIPT_DIR/remote-collect.sh" > "$snap/raw.txt" 2> "$snap/stderr.txt"; then
      cat "$snap/stderr.txt" >&2
      mv "$snap" "$snap.failed"
      die "collection failed; partial output kept in $snap.failed"
    fi
    grep -q '^=====SECTION meta=====' "$snap/raw.txt" || { mv "$snap" "$snap.failed"; die "no collector output; see $snap.failed"; }
    rc=0; finish_snapshot "$target" "$snap" || rc=$?; exit $rc ;;
  import)
    target=$(resolve_target "${1:-}"); raw="${2:-}"
    [ -f "$raw" ] || die "import needs a raw collector output file"
    snap=$(new_snapdir "$target")
    cp "$raw" "$snap/raw.txt"; : > "$snap/stderr.txt"
    rc=0; finish_snapshot "$target" "$snap" || rc=$?; exit $rc ;;
  diff)
    target=$(resolve_target "${1:-}"); hd=$(host_dir "$target")
    if [ $# -ge 3 ]; then old="$hd/$2"; new="$hd/$3"
    else
      set -- $(snapshots "$hd" | tail -2)
      [ $# -eq 2 ] || die "need two snapshots in $hd"
      old="$hd/$1"; new="$hd/$2"
    fi
    run_diff "$old" "$new" ;;
  findings)
    [ -n "${1:-}" ] || die "findings needs a snapshot directory"
    run_findings "$1" ;;
  list)
    target=$(resolve_target "${1:-}"); hd=$(host_dir "$target")
    for s in $(snapshots "$hd"); do
      printf '%s  %s ALERT  %s WARN  %s\n' "$s" \
        "$(grep -c '^ALERT' "$hd/$s/findings.txt" 2>/dev/null || true)" \
        "$(grep -c '^WARN' "$hd/$s/findings.txt" 2>/dev/null || true)" \
        "$(grep -E '^# (result|changed):' "$hd/$s/diff.txt" 2>/dev/null | sed 's/^# //' || echo 'first snapshot')"
    done ;;
  *) usage ;;
esac
