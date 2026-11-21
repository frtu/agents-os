#!/usr/bin/env python3
"""
arch_lib — atomic utils for architecture-reverse-engineering (no CLI, no I/O policy).

Each function does one action and raises on error; the scripts (scan_repo.py,
check_diagram.py) decide what to do with the result. Stdlib only.

Groups:
  Signals     load_signals, merge_signals, compile_signals
  Files       glob_matches, file_kind, inventory_reveals, iter_repo_files, is_binary, read_text
  Scanning    redact, scan_text, is_noise, extract_specs
  Documents   template_headings, doc_headings, mermaid_blocks, cited_paths
  Mermaid     lint_mermaid
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

REQUIRED_KEYS = ("version", "skip_dirs", "skip_files", "file_kinds", "inventory",
                 "categories", "runtime_specs", "secret_key_regex")
TIERS = ("confident", "flag")
SNIPPET_MAX = 160


class SignalsError(ValueError):
    """The signals config is missing, unreadable or has the wrong shape."""


# --------------------------------------------------------------------------- #
# Signals
# --------------------------------------------------------------------------- #

def load_signals(path: Path | str) -> dict:
    """Read and shape-check a signals JSON file; return it as a dict."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SignalsError(f"signals file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SignalsError(f"signals file is not valid JSON: {path}: {exc}") from exc
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        raise SignalsError(f"signals file {path} lacks keys: {', '.join(missing)}")
    for name, cat in data["categories"].items():
        if "bucket" not in cat:
            raise SignalsError(f"category {name!r} has no bucket")
        if not cat.get("patterns") and not cat.get("flag_patterns"):
            raise SignalsError(f"category {name!r} has neither patterns nor flag_patterns")
    return data


def merge_signals(base: dict, overlay: dict) -> dict:
    """Return base + overlay: lists are appended, categories merged by name.

    An overlay only needs the keys it adds to (e.g. {"categories": {"x": {...}}}).
    Scalars in the overlay (max_file_bytes, secret_key_regex) replace the base value.
    """
    out = json.loads(json.dumps(base))
    for key, value in overlay.items():
        if key in ("version", "description", "rules"):
            continue
        if key == "categories":
            for name, cat in value.items():
                tgt = out["categories"].setdefault(name, {"bucket": cat.get("bucket", "")})
                for k, v in cat.items():
                    if isinstance(v, list):
                        tgt[k] = list(tgt.get(k, [])) + v
                    else:
                        tgt[k] = v
        elif isinstance(value, list):
            out[key] = list(out.get(key, [])) + value
        else:
            out[key] = value
    return out


@dataclass
class Category:
    name: str
    bucket: str
    scopes: tuple[str, ...] | None
    confident: list[re.Pattern]
    flag: list[re.Pattern]


@dataclass
class Compiled:
    skip_dirs: set[str]
    skip_files: list[str]
    max_file_bytes: int
    file_kinds: list[tuple[str, list[str]]]
    inventory: list[tuple[str, str]]
    categories: list[Category]
    noise: list[dict]
    specs: list[dict]
    secret_key: re.Pattern


def compile_signals(signals: dict) -> Compiled:
    """Compile every regex once; raise SignalsError naming the first bad pattern."""
    def rx(pattern: str, where: str, flags: int = re.IGNORECASE) -> re.Pattern:
        try:
            return re.compile(pattern, flags)
        except re.error as exc:
            raise SignalsError(f"bad regex in {where}: {pattern!r}: {exc}") from exc

    cats = []
    for name, cat in signals["categories"].items():
        scopes = tuple(cat["scopes"]) if cat.get("scopes") else None
        cats.append(Category(
            name=name, bucket=cat["bucket"], scopes=scopes,
            confident=[rx(p, f"categories.{name}.patterns") for p in cat.get("patterns", [])],
            flag=[rx(p, f"categories.{name}.flag_patterns") for p in cat.get("flag_patterns", [])],
        ))
    noise = []
    for i, entry in enumerate(signals.get("known_noise", [])):
        noise.append({
            "path": entry.get("path"),
            "match": rx(entry["match"], f"known_noise[{i}]") if entry.get("match") else None,
            "category": entry.get("category"),
        })
    specs = [{"spec": s["spec"], "files": s["files"],
              "regex": rx(s["regex"], f"runtime_specs.{s['spec']}", re.IGNORECASE | re.MULTILINE)}
             for s in signals["runtime_specs"]]
    return Compiled(
        skip_dirs=set(signals["skip_dirs"]),
        skip_files=list(signals["skip_files"]),
        max_file_bytes=int(signals.get("max_file_bytes", 1_000_000)),
        file_kinds=[(k["kind"], k["globs"]) for k in signals["file_kinds"]],
        inventory=[(i["glob"], i["reveals"]) for i in signals["inventory"]],
        categories=cats,
        noise=noise,
        specs=specs,
        secret_key=rx(signals["secret_key_regex"], "secret_key_regex"),
    )


# --------------------------------------------------------------------------- #
# Files
# --------------------------------------------------------------------------- #

def glob_matches(rel: str, pattern: str) -> bool:
    """Match a repo-relative posix path against a signals glob.

    No '/' in the glob -> match the basename. With '/' -> match the path or any
    sub-path ('helm/*' matches 'helm/values.yaml' and 'deploy/helm/values.yaml').
    """
    if "/" not in pattern:
        return fnmatch.fnmatch(rel.rsplit("/", 1)[-1], pattern)
    return fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(rel, "*/" + pattern)


def file_kind(rel: str, compiled: Compiled) -> str | None:
    """Return the first file kind whose glob matches, or None (file not scanned)."""
    for kind, globs in compiled.file_kinds:
        if any(glob_matches(rel, g) for g in globs):
            return kind
    return None


def inventory_reveals(rel: str, compiled: Compiled) -> str | None:
    """Return what an inventory file reveals, or None if it isn't an inventory file."""
    for glob, reveals in compiled.inventory:
        if glob_matches(rel, glob):
            return reveals
    return None


def iter_repo_files(root: Path, compiled: Compiled) -> Iterator[tuple[str, Path]]:
    """Yield (relative posix path, absolute path) for every file not skipped, sorted."""
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in compiled.skip_dirs)
        for name in sorted(filenames):
            if any(fnmatch.fnmatch(name, g) for g in compiled.skip_files):
                continue
            full = Path(dirpath) / name
            if full.is_symlink():
                continue
            rel = full.relative_to(root).as_posix()
            yield rel, full


def is_binary(path: Path) -> bool:
    """True when the first 4 KiB contain a NUL byte."""
    with open(path, "rb") as fh:
        return b"\0" in fh.read(4096)


def read_text(path: Path) -> str:
    """Read a file as UTF-8, replacing undecodable bytes."""
    return path.read_text(encoding="utf-8", errors="replace")


# --------------------------------------------------------------------------- #
# Scanning
# --------------------------------------------------------------------------- #

_ASSIGN = re.compile(r"""^(?P<key>[^:=]*?)(?P<sep>\s*[:=]\s*)(?P<val>.+)$""")
_PLACEHOLDER = re.compile(r"""^["']?(\$\{|\{\{|<|%\(|\$[A-Z_])""")


def redact(line: str, secret_key: re.Pattern) -> str:
    """Hide the value of a `key: value` / `key=value` line whose key looks secret.

    'db.password: hunter2' -> 'db.password: <redacted>'; placeholders such as
    '${DB_PASSWORD}' are kept. The result is trimmed to SNIPPET_MAX characters.
    """
    text = line.strip()
    m = _ASSIGN.match(text)
    if m and secret_key.search(m.group("key")) and not _PLACEHOLDER.match(m.group("val").strip()):
        text = f"{m.group('key')}{m.group('sep')}<redacted>"
    if len(text) > SNIPPET_MAX:
        text = text[:SNIPPET_MAX - 1] + "…"
    return text


def is_noise(rel: str, category: str, matched: str, compiled: Compiled) -> bool:
    """True when a known_noise entry drops this hit (every condition it gives holds)."""
    for entry in compiled.noise:
        if entry["category"] and entry["category"] != category:
            continue
        if entry["path"] and not glob_matches(rel, entry["path"]):
            continue
        if entry["match"] and not entry["match"].search(matched):
            continue
        if entry["path"] or entry["match"]:
            return True
    return False


@dataclass
class Hit:
    bucket: str
    category: str
    tier: str
    path: str
    match: str
    lines: list[int] = field(default_factory=list)
    snippet: str = ""


def scan_text(text: str, rel: str, kind: str, compiled: Compiled) -> list[Hit]:
    """Grep one file's text with every category that applies to its kind.

    One Hit per (category, tier, lower-cased match) in the file, with every line
    number; a line that matches a confident pattern is not reported again as flag
    for the same category. Snippets are redacted.
    """
    hits: dict[tuple[str, str, str], Hit] = {}
    lines = text.splitlines()
    for cat in compiled.categories:
        if cat.scopes is not None and kind not in cat.scopes:
            continue
        for lineno, line in enumerate(lines, start=1):
            confident_here = False
            for tier, patterns in (("confident", cat.confident), ("flag", cat.flag)):
                if tier == "flag" and confident_here:
                    break
                for pat in patterns:
                    m = pat.search(line)
                    if not m:
                        continue
                    matched = m.group(0).strip()
                    if is_noise(rel, cat.name, matched, compiled):
                        continue
                    if tier == "confident":
                        confident_here = True
                    key = (cat.name, tier, matched.lower())
                    hit = hits.get(key)
                    if hit is None:
                        hit = hits[key] = Hit(cat.bucket, cat.name, tier, rel, matched,
                                              snippet=redact(line, compiled.secret_key))
                    if lineno not in hit.lines:
                        hit.lines.append(lineno)
    return list(hits.values())


@dataclass
class Spec:
    spec: str
    value: str
    path: str
    line: int


def extract_specs(text: str, rel: str, compiled: Compiled) -> list[Spec]:
    """Return every runtime spec whose extractor applies to this file."""
    out: list[Spec] = []
    seen: set[tuple[str, str]] = set()
    for ex in compiled.specs:
        if not any(glob_matches(rel, g) for g in ex["files"]):
            continue
        for m in ex["regex"].finditer(text):
            groups = [g for g in m.groups() if g] if m.groups() else []
            value = (groups[0] if groups else m.group(0)).strip()
            value = redact(value, compiled.secret_key)
            if (ex["spec"], value) in seen:
                continue
            seen.add((ex["spec"], value))
            out.append(Spec(ex["spec"], value, rel, text.count("\n", 0, m.start()) + 1))
    return out


# --------------------------------------------------------------------------- #
# Documents
# --------------------------------------------------------------------------- #

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_BRACKETS = re.compile(r"\[[^\]]*\]")


def _norm_heading(text: str) -> str:
    """'Runtime specs [optional]' -> 'runtime specs'."""
    return re.sub(r"\s+", " ", _BRACKETS.sub("", text)).strip().lower()


def template_headings(template: str, level: int = 2) -> list[str]:
    """Headings of the given level inside the template's first ````markdown skeleton.

    Headings are normalised (lower case, [bracketed] guidance removed) so the doc
    may fill them with real text.
    """
    out, inside = [], False
    for line in template.splitlines():
        if not inside and line.startswith("````markdown"):
            inside = True
            continue
        if inside and line.startswith("````"):
            break
        if inside:
            m = _HEADING.match(line)
            if m and len(m.group(1)) == level:
                out.append(_norm_heading(m.group(2)))
    return out


def doc_headings(md: str, level: int = 2) -> list[str]:
    """Normalised headings of the given level in a Markdown doc, outside code fences."""
    out, fence = [], False
    for line in md.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = _HEADING.match(line)
        if m and len(m.group(1)) == level:
            out.append(_norm_heading(m.group(2)))
    return out


def mermaid_blocks(md: str) -> list[tuple[int, str]]:
    """Return (first line number, body) for every ```mermaid block."""
    out, start, body = [], None, []
    for lineno, line in enumerate(md.splitlines(), start=1):
        stripped = line.strip()
        if start is None and stripped.startswith("```mermaid"):
            start, body = lineno + 1, []
        elif start is not None and stripped.startswith("```"):
            out.append((start, "\n".join(body)))
            start = None
        elif start is not None:
            body.append(line)
    return out


_CODE_SPAN = re.compile(r"`([^`\n]+)`")
_PATHLIKE = re.compile(r"^[\w.@~-][\w./@+-]*$")


def cited_paths(md: str) -> list[tuple[int, str]]:
    """Return (line, path) for every `code span` outside fences that looks like a repo path.

    A path has a '/' or ends in a file extension; a trailing ':12' or ':12-40' is
    dropped. URLs, globs, placeholders and option flags are ignored.
    """
    out, fence = [], False
    for lineno, line in enumerate(md.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        for m in _CODE_SPAN.finditer(line):
            token = re.sub(r":\d+(-\d+)?(,\d+)*$", "", m.group(1).strip())
            if not token or "://" in token or token.startswith(("-", "/", "~")):
                continue
            if not _PATHLIKE.match(token) or "*" in token:
                continue
            if "/" in token or re.search(r"\.[A-Za-z][A-Za-z0-9]{0,9}$", token):
                if re.match(r"^\d+(\.\d+)+$", token):        # a version, not a file
                    continue
                out.append((lineno, token))
    return out


# --------------------------------------------------------------------------- #
# Mermaid
# --------------------------------------------------------------------------- #

# (opener, closer), longest first so '[(' wins over '['.
_SHAPES = [("[(", ")]"), ("([", "])"), ("[[", "]]"), ("((", "))"), ("{{", "}}"),
           ("[/", "/]"), ("[\\", "\\]"), ("[", "]"), ("(", ")"), ("{", "}")]
_NODE_START = re.compile(r"(?:^|(?<=[\s;&>|-]))([A-Za-z_]\w*)(?=[\[({])")
_EDGE_LABEL = re.compile(r"\|[^|]*\|")
_KEYWORDS = {"subgraph", "end", "classdef", "class", "style", "linkstyle", "click",
             "direction", "flowchart", "graph"}


@dataclass
class Finding:
    code: str
    line: int
    message: str


def _node_defs(line: str) -> Iterator[tuple[str, str, bool]]:
    """Yield (node id, label, quoted) for each node definition on a flowchart line.

    Edge labels (|...|) are blanked first; scanning resumes after each shape, so
    text inside a label is never read as another node.
    """
    line = _EDGE_LABEL.sub("||", line)
    pos = 0
    while True:
        m = _NODE_START.search(line, pos)
        if not m:
            return
        node_id, rest = m.group(1), line[m.end():]
        pos = m.end()
        if node_id.lower() in _KEYWORDS:
            continue
        for opener, closer in _SHAPES:
            if not rest.startswith(opener):
                continue
            body = rest[len(opener):]
            if body.startswith('"'):
                end_q = body.find('"', 1)
                label = body[1:end_q] if end_q > 0 else body[1:]
                tail = body.find(closer, end_q + 1 if end_q > 0 else 1)
                quoted = True
            else:
                tail = body.find(closer)
                label = body[:tail] if tail >= 0 else body
                quoted = False
            consumed = len(opener) + (tail + len(closer) if tail >= 0 else len(body))
            pos = m.end() + consumed
            yield node_id, label, quoted
            break


def lint_mermaid(text: str, first_line: int = 1) -> list[Finding]:
    """Static checks on a flowchart block; return findings (empty = clean).

    UNBALANCED     'subgraph' and 'end' counts differ
    DUP_ID         one node id defined with two different labels
    UNQUOTED_CHARS an unquoted label contains ( ) [ ] { } (wrap it in double quotes)
    UNKNOWN_CLASS  'class x name' or ':::name' uses a classDef that isn't defined
    """
    findings: list[Finding] = []
    opened = closed = 0
    labels: dict[str, tuple[str, int]] = {}
    class_defs: set[str] = set()
    class_uses: list[tuple[str, int]] = []
    for offset, raw in enumerate(text.splitlines()):
        lineno = first_line + offset
        line = raw.split("%%", 1)[0].strip()
        if not line:
            continue
        low = line.lower()
        if re.match(r"^subgraph\b", low):
            opened += 1
            continue
        if low == "end":
            closed += 1
            continue
        m = re.match(r"^classdef\s+([\w,-]+)", low)
        if m:
            class_defs.update(c for c in line.split()[1].split(","))
            continue
        m = re.match(r"^class\s+\S+\s+([\w-]+)", line)
        if m:
            class_uses.append((m.group(1), lineno))
            continue
        if re.match(r"^(style|linkstyle|click|direction|flowchart|graph)\b", low):
            continue
        for name in re.findall(r":::([\w-]+)", line):
            class_uses.append((name, lineno))
        for node_id, label, quoted in _node_defs(line):
            if not quoted and re.search(r"[()\[\]{}]", label):
                findings.append(Finding("UNQUOTED_CHARS", lineno,
                                        f"label of {node_id} has brackets; wrap it in double quotes"))
            prev = labels.get(node_id)
            if prev and prev[0] != label:
                findings.append(Finding("DUP_ID", lineno,
                                        f"{node_id} already defined on line {prev[1]} with another label"))
            elif not prev:
                labels[node_id] = (label, lineno)
    if opened != closed:
        findings.append(Finding("UNBALANCED", first_line,
                                f"{opened} subgraph vs {closed} end"))
    for name, lineno in class_uses:
        if name not in class_defs:
            findings.append(Finding("UNKNOWN_CLASS", lineno, f"classDef {name!r} is not defined"))
    return findings
