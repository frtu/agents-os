"""Tests for check_diagram. Run: ./architecture-reverse-engineering.sh --test"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import check_diagram
from _fixture import make_repo

GOOD = """# Orders service — component diagram

> Reverse-engineered from the code at working tree on 2026-01-01.

## Summary

Synthetic service.

## Component diagram

```mermaid
flowchart TB
    subgraph SVC["Orders"]
        api(["API"])
    end
    api -->|SQL| db[("Orders DB")]
    classDef service fill:#dbeafe
    class api service
```

## Flows in a nutshell

1. Client → api → db

## Components and evidence

| Component | Layer | Kind | What flows | Auth | Evidence |
| --- | --- | --- | --- | --- | --- |
| Orders DB | middleware | database | orders | password | `src/main/resources/application.yml:3` |

## Runtime specs

| Spec | Value | Evidence |
| --- | --- | --- |
| Base image | zulu-openjdk:21-jre | `Dockerfile` |

## Components not defined in this repo

None found.
"""


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = check_diagram.main(argv)
    return code, out.getvalue(), err.getvalue()


class CheckDiagramTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(Path(self.tmp.name))
        self.doc = self.root / "docs" / "architecture" / "component-diagram.md"
        self.doc.parent.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, text, *extra):
        self.doc.write_text(text, encoding="utf-8")
        code, out, _ = run([str(self.doc), "--repo", str(self.root), "--json", *extra])
        return code, json.loads(out)

    def test_good_doc_passes(self):
        code, report = self.check(GOOD)
        self.assertEqual(report["findings"], [])
        self.assertEqual(code, 0)

    def test_missing_section_and_evidence(self):
        bad = GOOD.replace("## Runtime specs", "## Specs").replace("`Dockerfile`", "`Dockerfile.prod`")
        code, report = self.check(bad)
        self.assertEqual(code, 1)
        codes = {f["code"] for f in report["findings"]}
        self.assertEqual(codes, {"MISSING_SECTION", "MISSING_EVIDENCE"})

    def test_no_mermaid(self):
        bad = GOOD.split("```mermaid")[0] + GOOD.split("```\n", 2)[-1]
        code, report = self.check(bad)
        self.assertEqual(code, 1)
        self.assertIn("NO_MERMAID", {f["code"] for f in report["findings"]})

    def test_template_drives_sections(self):
        tpl = self.root / "tpl.md"
        tpl.write_text("````markdown\n# X\n## Summary\n## Risks\n````\n", encoding="utf-8")
        code, report = self.check(GOOD, "--template", str(tpl))
        self.assertEqual(code, 1)
        self.assertEqual([f["message"] for f in report["findings"]], ["missing section '## risks'"])

    def test_text_mode_and_bad_args(self):
        self.doc.write_text(GOOD, encoding="utf-8")
        code, out, _ = run([str(self.doc)])
        self.assertEqual((code, out.startswith("OK")), (0, True))
        code, _, _ = run([str(self.root / "missing.md")])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
