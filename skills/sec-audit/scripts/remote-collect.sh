#!/usr/bin/env bash
# remote-collect.sh — intrusion-diagnostic collector. Runs ON the audited Linux host.
#
# Read-only: it changes nothing on the host. It prints sections to stdout, each starting
# with a line "=====SECTION <name>=====". sec-audit.sh splits them into one file per
# section, so each section must be deterministic (sorted, no PIDs or timestamps) unless
# it is listed in VOLATILE_SECTIONS in sec-audit.sh.
#
# Usage (normally piped over SSH by sec-audit.sh):
#   bash remote-collect.sh [--quick]
#     --quick   skip the slow checks (setuid scan, package integrity), ~10s instead of ~90s
#
# It uses passwordless sudo when available ("sudo -n"); otherwise it collects what the
# login user can see and reports sudo=no in the meta section.

set -u
export LC_ALL=C
export PATH="$PATH:/usr/local/sbin:/usr/sbin:/sbin"
QUICK=0
[ "${1:-}" = "--quick" ] && QUICK=1

if sudo -n true 2>/dev/null; then S="sudo -n"; SUDO=yes; else S=""; SUDO=no; fi

sec() { printf '=====SECTION %s=====\n' "$1"; }
# Run a shell snippet as root when possible (globs then expand with root's view).
rsh() { $S sh -c "$1"; }

# ---------------------------------------------------------------- meta (volatile)
sec meta
echo "collected_at=$(date -Is)"
echo "hostname=$(hostname)"
echo "kernel=$(uname -srm)"
. /etc/os-release 2>/dev/null && echo "os=${PRETTY_NAME:-unknown}"
echo "uptime=$(uptime -p 2>/dev/null)"
echo "login_user=$(id -un)"
echo "sudo=$SUDO"
echo "quick=$QUICK"

# ---------------------------------------------------------------- accounts
sec users
getent passwd | awk -F: '$3==0 || ($3>=1000 && $3<65534) || $7 !~ /(nologin|false|sync|halt|shutdown)$/ {print $1":"$3":"$4":"$6":"$7}' | sort
echo "# uid0: $(getent passwd | awk -F: '$3==0{printf "%s ", $1}')"
for g in sudo adm wheel docker root; do getent group "$g"; done
echo "# empty-password accounts:"
rsh "awk -F: '\$2==\"\"{print \$1}' /etc/shadow 2>/dev/null" | sort

sec sudoers
rsh "cat /etc/sudoers /etc/sudoers.d/* 2>/dev/null" | grep -vE '^[[:space:]]*(#|$)' | sort

sec ssh_keys
# Fingerprints only: never copy key material into the audit history.
for h in /root $(getent passwd | awk -F: '$3>=1000 && $3<65534 {print $6}'); do
  for f in "$h/.ssh/authorized_keys" "$h/.ssh/authorized_keys2"; do
    $S test -f "$f" || continue
    echo "# $f"
    $S ssh-keygen -lf "$f" 2>/dev/null || echo "(unparseable entries)"
  done
done

sec sshd
$S sshd -T 2>/dev/null | grep -E '^(port|listenaddress|permitrootlogin|passwordauthentication|kbdinteractiveauthentication|pubkeyauthentication|permitemptypasswords|authorizedkeysfile|allowusers|allowgroups|maxauthtries|x11forwarding) ' | sort
echo "# drop-ins: $(ls -1 /etc/ssh/sshd_config.d/ 2>/dev/null | tr '\n' ' ')"

# ---------------------------------------------------------------- logins
# Unique (result, method, user, source) tuples over 30 days: stable, so a new source IP shows in the diff.
SSHLOG=$($S journalctl -u ssh -u sshd --since "-30 days" --no-pager -o cat 2>/dev/null)
sec auth_sources
printf '%s\n' "$SSHLOG" | awk '
  /^Accepted /           { for(i=1;i<=NF;i++){ if($i=="for")u=$(i+1); if($i=="from")ip=$(i+1) } print "accepted", $2, u, ip; next }
  /^Failed /             { for(i=1;i<=NF;i++){ if($i=="from")ip=$(i+1) } u=($4=="invalid")?"invalid:"$6:$4; print "failed", $2, u, ip; next }
  /^Invalid user /       { for(i=1;i<=NF;i++){ if($i=="from")ip=$(i+1) } print "invalid", "-", $3, ip }' | sort -u

sec auth_counts
printf '%s\n' "$SSHLOG" | awk '/^Accepted /{a++} /^Failed /{f++} /^Invalid user /{i++} END{print "accepted_30d="a+0; print "failed_30d="f+0; print "invalid_user_30d="i+0}'

sec logins
last -n 30 -a -w 2>/dev/null | grep -v '^$'

sec failed_logins
$S lastb -n 30 -a -w 2>/dev/null | grep -v '^$'

# ---------------------------------------------------------------- network
sec listeners
# proto, local address, process names (PIDs and fds stripped so the diff is stable)
$S ss -H -tulpn 2>/dev/null | awk '{p=$7; gsub(/,pid=[0-9]+,fd=[0-9]+/,"",p); print $1, $5, p}' | sort -u

sec connections
$S ss -H -tnp state established 2>/dev/null | awk '{p=$5; gsub(/,pid=[0-9]+,fd=[0-9]+/,"",p); print $4, p}' | sort | uniq -c

sec network
ip -br addr 2>/dev/null | grep -vE '^(veth|br-)' | awk '{$2=""; print}' | sort
ip route 2>/dev/null | grep -vE 'linkdown' | sort
echo "# resolv.conf"; grep -vE '^[[:space:]]*(#|$)' /etc/resolv.conf 2>/dev/null
echo "# hosts";       grep -vE '^[[:space:]]*(#|$)' /etc/hosts 2>/dev/null

sec firewall
# Counters and timestamps stripped so only rule changes show in the diff.
if command -v iptables-save >/dev/null 2>&1; then
  $S iptables-save 2>/dev/null | grep -vE '^#' | sed -E 's/\[[0-9]+:[0-9]+\]//'
elif command -v nft >/dev/null 2>&1; then
  $S nft list ruleset 2>/dev/null | grep -vE '^[[:space:]]*$' | sed -E 's/ counter packets [0-9]+ bytes [0-9]+//; s/ *# handle [0-9]+//'
fi
command -v ufw >/dev/null 2>&1 && $S ufw status 2>/dev/null

# ---------------------------------------------------------------- persistence
sec cron
for u in $(getent passwd | cut -d: -f1); do
  c=$($S crontab -l -u "$u" 2>/dev/null | grep -vE '^[[:space:]]*(#|$)')
  [ -n "$c" ] && { echo "# user $u"; printf '%s\n' "$c"; }
done
echo "# /etc/crontab"
grep -vhE '^[[:space:]]*(#|$)' /etc/crontab 2>/dev/null
for d in /etc/cron.d /etc/cron.hourly /etc/cron.daily /etc/cron.weekly /etc/cron.monthly; do
  ls -1A "$d" 2>/dev/null | sed "s|^|$d/|"
done
echo "# at jobs"; $S atq 2>/dev/null | awk '{print $NF, $0}' | cut -d' ' -f2- | sort

sec timers
systemctl list-timers --all --no-legend --plain 2>/dev/null | awk '{print $(NF-1), $NF}' | sort -u

sec services
echo "# enabled"
systemctl list-unit-files --type=service --state=enabled --no-legend --plain 2>/dev/null | awk '{print $1}' | sort
echo "# running"
systemctl list-units --type=service --state=running --no-legend --plain 2>/dev/null | awk '{print $1}' | sort

sec unit_files
# Hashes of locally-added units and autostart entries (packages install to /lib or /usr/lib).
rsh "find /etc/systemd/system /etc/systemd/user /etc/xdg/autostart /root/.config/systemd /root/.config/autostart /home/*/.config/systemd /home/*/.config/autostart -xdev -type f 2>/dev/null" \
  | sort | while IFS= read -r f; do $S sha256sum "$f"; done

sec persistence
echo "# /etc/ld.so.preload"; cat /etc/ld.so.preload 2>/dev/null || echo "(none)"
echo "# ssh rc/environment files"
rsh "ls -1 /root/.ssh/rc /root/.ssh/environment /home/*/.ssh/rc /home/*/.ssh/environment /etc/ssh/sshrc 2>/dev/null" || true
echo "# shell startup files (sha256)"
rsh "sha256sum /etc/profile /etc/bash.bashrc /etc/environment /etc/rc.local /etc/zsh/* /etc/profile.d/* \
  /root/.bashrc /root/.profile /root/.zshrc /root/.zprofile /root/.zshenv \
  /home/*/.bashrc /home/*/.bash_profile /home/*/.bash_login /home/*/.profile \
  /home/*/.zshrc /home/*/.zprofile /home/*/.zshenv /home/*/.zlogin 2>/dev/null" | sort -k2

sec rc_suspicious
# Lines in shell startup files that download, decode or open sockets: common backdoor shapes.
rsh "grep -HnE 'curl |wget |base64|/dev/tcp/|nc -|ncat |socat |python[0-9.]* -c|eval .*\\\$\\(' \
  /etc/profile /etc/bash.bashrc /etc/zsh/* /etc/profile.d/* /root/.bashrc /root/.profile /root/.zshrc \
  /home/*/.bashrc /home/*/.bash_profile /home/*/.profile /home/*/.zshrc /home/*/.zprofile /home/*/.zshenv 2>/dev/null" \
  | grep -vE '^[^:]+:[0-9]+:[[:space:]]*#' | grep -vE 'eval "?\$\((dircolors|ssh-agent|brew shellenv)' | sort

sec kernel_modules
lsmod 2>/dev/null | awk 'NR>1{print $1}' | sort

# ---------------------------------------------------------------- oh-my-zsh
sec omz
found=0
for d in $(rsh "ls -d /root/.oh-my-zsh /home/*/.oh-my-zsh 2>/dev/null"); do
  found=1
  g() { $S git -c 'safe.directory=*' -C "$d" "$@" 2>/dev/null; }
  echo "# $d"
  echo "remote=$(g remote get-url origin)"
  echo "branch=$(g rev-parse --abbrev-ref HEAD)"
  echo "installed=$($S stat -c %w "$d" 2>/dev/null | cut -d. -f1)"
  echo "dirty_files:"
  g status --porcelain | sed 's/^/  /'
  echo "custom_files:"
  $S find "$d/custom" -type f ! -name 'example.zsh' ! -name 'example.zsh-theme' ! -path '*/example/*' 2>/dev/null | sort | sed 's/^/  /'
done
[ "$found" = 0 ] && echo "(no oh-my-zsh installation)"

# ---------------------------------------------------------------- software
sec packages
dpkg-query -W -f='${Package} ${Version}\n' 2>/dev/null | sort

sec apt_history
zcat -f /var/log/apt/history.log* 2>/dev/null | awk '
  /^Start-Date:/   { d=$2" "$3 }
  /^Commandline:/  { sub(/^Commandline: /,""); c=$0 }
  /^Requested-By:/ { sub(/^Requested-By: /,""); r=$0 }
  /^End-Date:/     { print d " | " c " | " (r==""?"-":r); c=""; r="" }' | sort | tail -50

sec docker
if command -v docker >/dev/null 2>&1; then
  echo "# containers (name image)"; $S docker ps -a --format '{{.Names}} {{.Image}}' 2>/dev/null | sort
  echo "# images"; $S docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' 2>/dev/null | sort
fi

sec processes
# Unique user+command, without kernel threads (children of kthreadd, pid 2) and without
# this collector's own session (ps, sort, sudo, ...), so the diff shows new daemons only.
MYSID=$(ps -o sid= -p $$ | tr -d ' ')
ps --ppid 2 -p 2 -N -o sid=,user=,comm= 2>/dev/null | awk -v me="$MYSID" '$1!=me {print $2, $3}' | sort -u

sec suspicious_procs
# Processes whose binary is deleted or lives in a temp dir. "(deleted)" is also normal for
# daemons still running an old binary after an upgrade: a reboot or restart clears those.
rsh 'for p in /proc/[0-9]*; do e=$(readlink "$p/exe" 2>/dev/null) || continue
  case "$e" in *"(deleted)"*|/tmp/*|/var/tmp/*|/dev/shm/*)
    echo "${p#/proc/} $e :: $(tr "\0" " " < "$p/cmdline" 2>/dev/null | cut -c1-120)";; esac; done'

sec tmp_files
echo "# executables"
$S find /tmp /var/tmp /dev/shm -xdev -type f -perm /111 2>/dev/null | sort
echo "# hidden entries"
$S find /tmp /var/tmp /dev/shm -xdev -name '.*' ! -name '.X*-lock' ! -name '.X11-unix' ! -name '.ICE-unix' ! -name '.font-unix' ! -name '.XIM-unix' ! -name '.Test-unix' 2>/dev/null | sort

sec recent_changes
# System files modified in the last 7 days (volatile: apt upgrades show up here too).
$S find /etc /usr/bin /usr/sbin /usr/local /usr/lib/systemd -xdev -type f -mtime -7 -printf '%TY-%Tm-%Td %p\n' 2>/dev/null | sort | tail -200

sec logging
echo "storage=$(systemd-analyze cat-config systemd/journald.conf 2>/dev/null | grep -E '^Storage=' | tail -1 | cut -d= -f2)"
echo "persistent_dir=$( [ -d /var/log/journal ] && ls /var/log/journal 2>/dev/null | grep -q . && echo yes || echo no)"

# ---------------------------------------------------------------- slow checks
if [ "$QUICK" = 0 ]; then
  sec suid
  $S find / -xdev \( -perm -4000 -o -perm -2000 \) -type f -printf '%m %u %p\n' 2>/dev/null | sort -k3

  sec integrity
  # Package files whose checksum no longer matches dpkg's record. Conffiles (" c ") are
  # excluded: admins edit those. A changed binary in /usr/bin or /usr/lib is a red flag.
  $S dpkg -V 2>/dev/null | grep -v ' c /' | sort -k2
fi
