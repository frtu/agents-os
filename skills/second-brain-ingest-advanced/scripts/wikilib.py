#!/usr/bin/env python3
"""Shared helpers for second-brain-ingest-advanced scripts (stdlib only).

A "vault dir" is the folder that contains `wiki/` (and usually `raw/`, `output/`, `docs/`).
All paths stored in run files are POSIX paths relative to the vault dir.
"""

import hashlib
import json
import os
import re
import subprocess

TRACKED_DIRS = ("wiki", "output")
WIKILINK = re.compile(r"\[\[([^\[\]]+?)\]\]")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def read_text(path, default=""):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return f.read()


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(vault, path):
    return os.path.relpath(os.path.abspath(path), os.path.abspath(vault)).replace(os.sep, "/")


def iter_files(vault, dirs=TRACKED_DIRS, ext=".md"):
    """Yield vault-relative paths of files under the given top-level dirs."""
    for d in dirs:
        root = os.path.join(vault, d)
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(x for x in dirnames if not x.startswith("."))
            for name in sorted(filenames):
                if ext is None or name.endswith(ext):
                    yield rel(vault, os.path.join(dirpath, name))


def snapshot(vault):
    """{relpath: sha1} for every markdown file in the tracked dirs."""
    return {p: sha1(os.path.join(vault, p)) for p in iter_files(vault)}


def link_targets(vault):
    """Names a same-vault wikilink may resolve to: md basenames without extension,
    plus full basenames of any other file under the vault (pdf, png, ...)."""
    names = set()
    for dirpath, dirnames, filenames in os.walk(vault):
        dirnames[:] = [x for x in dirnames if not x.startswith(".")]
        for name in filenames:
            names.add(name[:-3] if name.endswith(".md") else name)
    return names


def slug_index(vault):
    """{folder relative to wiki/: [slugs]} for every wiki page."""
    index = {}
    for p in iter_files(vault, dirs=("wiki",)):
        folder, name = os.path.split(p[len("wiki/"):])
        index.setdefault(folder or ".", []).append(name[:-3])
    return index


def parse_link(raw):
    """'target#anchor|Display' (pipe may be escaped as \\|) -> target."""
    target = re.split(r"\\?\|", raw, maxsplit=1)[0]
    return target.split("#", 1)[0].strip()


def vault_name(vault):
    """The vault's display name: parent folder when the vault dir is literally 'vault'."""
    absv = os.path.abspath(vault)
    base = os.path.basename(absv)
    return os.path.basename(os.path.dirname(absv)) if base == "vault" else base


def git_root(vault):
    try:
        out = subprocess.run(["git", "-C", vault, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def git_dirty(vault):
    """Vault-relative paths that are modified/untracked in git (empty if not a repo)."""
    root = git_root(vault)
    if not root:
        return []
    out = subprocess.run(["git", "-C", root, "status", "--porcelain", "-z", "--untracked-files=all"],
                         capture_output=True, text=True).stdout
    dirty = []
    for entry in out.split("\0"):
        if len(entry) < 4:
            continue
        path = os.path.join(root, entry[3:])
        r = rel(vault, path)
        if not r.startswith(".."):
            dirty.append(r)
    return sorted(set(dirty))


def in_scope(path, scopes):
    """True if path equals a scope file or sits under a scope dir (scope ends with '/')."""
    for s in scopes:
        if s.endswith("/") and path.startswith(s):
            return True
        if path == s:
            return True
    return False


def scopes_overlap(a, b):
    for x in a:
        for y in b:
            if x == y:
                return True
            if x.endswith("/") and y.startswith(x):
                return True
            if y.endswith("/") and x.startswith(y):
                return True
    return False
