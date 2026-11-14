"""Offline tests for sec-audit.sh: split, findings, known-benign allowlist and diff.

Run: python3 -m pytest sec-audit/scripts/test_sec_audit.py   (or: python3 test_sec_audit.py)
No SSH: snapshots are created with `sec-audit.sh import` from synthetic collector output.
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "sec-audit.sh"
COLLECTOR = HERE / "remote-collect.sh"
TARGET = "tester@host.example"

BASE = {
    "meta": "collected_at=2026-01-01T00:00:00\nhostname=testhost\nsudo=yes\nquick=0",
    "users": "root:0:0:/root:/bin/bash\nalice:1000:1000:/home/alice:/usr/bin/zsh\n# uid0: root \n# empty-password accounts:",
    "sudoers": "alice ALL=(ALL) NOPASSWD: ALL",
    "sshd": "passwordauthentication no\npermitrootlogin no\npermitemptypasswords no",
    "auth_sources": "accepted publickey alice 10.0.0.2",
    "auth_counts": "accepted_30d=4\nfailed_30d=0\ninvalid_user_30d=0",
    "listeners": "tcp 0.0.0.0:22 users:((\"sshd\"))\ntcp 127.0.0.1:631 users:((\"cupsd\"))",
    "persistence": "# /etc/ld.so.preload\n(none)\n# shell startup files (sha256)\nabc  /home/alice/.zshrc",
    "rc_suspicious": "",
    "tmp_files": "# executables\n# hidden entries",
    "suspicious_procs": "",
    "integrity": "??5??????   /usr/share/example-pkg/defaults.conf",
    "omz": "# /home/alice/.oh-my-zsh\nremote=https://github.com/ohmyzsh/ohmyzsh.git\nbranch=master\ndirty_files:\ncustom_files:",
    "logging": "storage=persistent\npersistent_dir=yes",
}


def raw(sections):
    return "".join(f"=====SECTION {k}=====\n{v}\n" for k, v in sections.items())


class SecAuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.hostdir = self.root / "audit" / TARGET

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, *args, ts=None):
        env = dict(os.environ, SEC_AUDIT_DIR=str(self.root / "audit"))
        if ts:
            env["SEC_AUDIT_TS"] = ts
        return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, env=env)

    def importsnap(self, sections, ts):
        f = self.root / f"{ts}.raw"
        f.write_text(raw(sections))
        return self.run_script("import", TARGET, str(f), ts=ts)

    def findings(self, ts):
        return (self.hostdir / ts / "findings.txt").read_text()

    def test_collector_and_driver_parse(self):
        for script in (SCRIPT, COLLECTOR):
            r = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_split_and_clean_findings(self):
        r = self.importsnap(BASE, "2026-01-01_000000")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        sec = self.hostdir / "2026-01-01_000000" / "sections"
        self.assertEqual((sec / "listeners.txt").read_text().count("\n"), 2)
        f = self.findings("2026-01-01_000000")
        self.assertIn("OK    sshd.password", f)
        self.assertIn("OK    omz.remote", f)
        self.assertIn("WARN  integrity", f)  # no allowlist yet
        self.assertIn("first snapshot", r.stdout)

    def test_alerts_set_exit_code(self):
        bad = dict(BASE)
        bad["users"] = BASE["users"].replace("# uid0: root ", "# uid0: root toor ")
        bad["omz"] = BASE["omz"].replace("ohmyzsh/ohmyzsh.git", "evil/ohmyzsh.git") + "\n  M lib/git.zsh"
        bad["persistence"] = BASE["persistence"].replace("(none)", "/usr/lib/libhide.so")
        bad["sshd"] = "passwordauthentication yes\npermitrootlogin yes"
        r = self.importsnap(bad, "2026-01-01_000000")
        self.assertEqual(r.returncode, 2, r.stdout)
        f = self.findings("2026-01-01_000000")
        for check in ("users.uid0", "omz.remote", "ld.so.preload", "sshd.root"):
            self.assertRegex(f, rf"ALERT\s+{check}")
        self.assertRegex(f, r"WARN\s+sshd.password")

    def test_known_benign_suppresses(self):
        self.hostdir.mkdir(parents=True)
        (self.hostdir / "known-benign.txt").write_text("# reason\n/usr/share/example-pkg/defaults.conf\n")
        self.importsnap(BASE, "2026-01-01_000000")
        f = self.findings("2026-01-01_000000")
        self.assertIn("OK    integrity", f)
        self.assertIn("1 line(s) suppressed", f)

    def test_diff_reports_stable_changes_only(self):
        self.importsnap(BASE, "2026-01-01_000000")
        nxt = dict(BASE)
        nxt["meta"] = BASE["meta"].replace("2026-01-01", "2026-01-08")  # volatile: ignored
        nxt["listeners"] = BASE["listeners"] + "\ntcp 0.0.0.0:4444 users:((\"nc\"))"
        r = self.importsnap(nxt, "2026-01-08_000000")
        diff = (self.hostdir / "2026-01-08_000000" / "diff.txt").read_text()
        self.assertIn("# changed: listeners", diff)
        self.assertIn("+tcp 0.0.0.0:4444", diff)
        self.assertNotIn("## meta", diff)
        self.assertIn("changed: listeners", r.stdout)
        # explicit diff command matches the auto diff
        r2 = self.run_script("diff", TARGET)
        self.assertIn("+tcp 0.0.0.0:4444", r2.stdout)

    def test_no_change(self):
        self.importsnap(BASE, "2026-01-01_000000")
        r = self.importsnap(BASE, "2026-01-02_000000")
        self.assertIn("no change in stable sections", r.stdout)
        lst = self.run_script("list", TARGET).stdout
        self.assertIn("2026-01-02_000000", lst)


if __name__ == "__main__":
    unittest.main()
