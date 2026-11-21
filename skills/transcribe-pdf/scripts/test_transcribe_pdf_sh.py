#!/usr/bin/env python3
"""Tests for the entry point transcribe-pdf.sh: --help passthrough and .env loading (run: ./transcribe-pdf.sh --test)."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_pdf_lib import make_pdf

SCRIPT = Path(__file__).resolve().parent / "transcribe-pdf.sh"


def run_sh(args, env_extra, cwd=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("TRANSCRIBE_PDF_")}
    for k in ("TRANSCRIBE_PDF_VENV", "TRANSCRIBE_PDF_PYTHON"):   # keep the venv the tests run in
        if k in os.environ:
            env[k] = os.environ[k]
    env.update(env_extra)
    return subprocess.run(["/bin/bash", str(SCRIPT), *args], capture_output=True, text=True,
                          env=env, cwd=cwd, timeout=300)


class TestEntryPoint(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.no_env = {"TRANSCRIBE_PDF_ENV_FILE": str(self.dir / "absent.env")}

    def tearDown(self):
        self._tmp.cleanup()

    def test_help_exits_0_from_any_directory(self):
        res = run_sh(["--help"], self.no_env, cwd=self.dir)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("usage: transcribe-pdf.sh", res.stdout)

    def test_password_loaded_from_env_file_and_shell_wins(self):
        pdf = make_pdf(self.dir / "l.pdf", ["Locked text"], user_pwd="pw")
        env_file = self.dir / ".env"
        env_file.write_text('# secrets\nTRANSCRIBE_PDF_PASSWORD="pw"\nOTHER_TOOL=1\n')
        args = [str(pdf), "--ocr", "never", "--json", "--force"]

        res = run_sh(args, self.no_env)
        self.assertEqual(json.loads(res.stdout)["results"][0]["status"], "locked")

        res = run_sh(args, {"TRANSCRIBE_PDF_ENV_FILE": str(env_file)})
        self.assertEqual(json.loads(res.stdout)["results"][0]["status"], "written", res.stderr)

        # a value already set in the shell wins over the file
        res = run_sh(args, {"TRANSCRIBE_PDF_ENV_FILE": str(env_file), "TRANSCRIBE_PDF_PASSWORD": "wrong"})
        self.assertEqual(json.loads(res.stdout)["results"][0]["status"], "locked")


if __name__ == "__main__":
    unittest.main()
