#!/usr/bin/env python3
"""
Relink Wiki Pages

Scans all wiki pages and adds wikilinks for mentions of concepts/entities/features
that have their own pages but aren't already linked.

Usage:
    python scripts/relink-wiki.py [--dry-run] [--verbose]
"""

import os
import re
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Wiki root directory
WIKI_ROOT = Path(__file__).parent.parent / "wiki"

# Folders to scan for content pages
CONTENT_FOLDERS = ["concepts", "product", "resources", "people", "projects", "synthesis"]

# Files to skip
SKIP_FILES = {"README.md", "log.md", "portal.md", "index.md"}

# Folders to skip
SKIP_FOLDERS = {"sources"}


def build_vocabulary() -> Dict[str, List[str]]:
    """
    Build a vocabulary mapping page slugs to their display name variations.
    Returns: {slug: [variations]}
    """
    vocab: Dict[str, List[str]] = {}

    for folder in CONTENT_FOLDERS:
        folder_path = WIKI_ROOT / folder
        if not folder_path.exists():
            continue

        for md_file in folder_path.rglob("*.md"):
            if md_file.name in SKIP_FILES:
                continue
            if any(skip in md_file.parts for skip in SKIP_FOLDERS):
                continue

            slug = md_file.stem  # filename without .md
            variations = generate_variations(slug)
            vocab[slug] = variations

    # Add common abbreviations and aliases
    aliases = {
        "elasticsearch": ["ES", "Elastic"],
        "clickhouse": ["CH"],
        "flink": ["Apache Flink"],
        "kafka": ["Apache Kafka"],
        "rag": ["Retrieval Augmented Generation", "Retrieval-Augmented Generation"],
        "ner": ["Named Entity Recognition"],
        "pos": ["Part of Speech", "Part-of-Speech"],
        "llm": ["Large Language Model", "Large Language Models"],
        "mcp": ["Model Context Protocol"],
        "bm25": ["Best Matching 25"],
        "tf-idf": ["Term Frequency-Inverse Document Frequency", "TFIDF"],
    }

    for slug, extra_vars in aliases.items():
        if slug in vocab:
            vocab[slug].extend(extra_vars)

    return vocab


def generate_variations(slug: str) -> List[str]:
    """
    Generate display name variations from a slug.
    e.g., "search-service" -> ["Search Service", "SearchService", "search service"]
    """
    variations = []

    # Title case with spaces: "search-service" -> "Search Service"
    title_case = " ".join(word.capitalize() for word in slug.split("-"))
    variations.append(title_case)

    # CamelCase: "search-service" -> "SearchService"
    camel_case = "".join(word.capitalize() for word in slug.split("-"))
    if camel_case != title_case.replace(" ", ""):
        variations.append(camel_case)

    # Original slug if single word and different
    if "-" not in slug and slug.lower() not in [v.lower() for v in variations]:
        variations.append(slug.capitalize())

    return variations


def find_existing_links(content: str) -> Set[str]:
    """
    Find all existing wikilinks in the content.
    Returns set of linked slugs (lowercased).
    """
    linked = set()

    # Match [[slug]] or [[slug|Display]]
    pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
    for match in re.finditer(pattern, content):
        link_target = match.group(1).strip()
        # Extract just the filename if it's a path
        if "/" in link_target:
            link_target = link_target.split("/")[-1]
        linked.add(link_target.lower())

    return linked


def find_unlinked_mentions(content: str, vocab: Dict[str, List[str]], existing_links: Set[str]) -> List[Tuple[str, str, str]]:
    """
    Find mentions in content that should be linked but aren't.
    Returns: [(original_text, slug, suggested_link)]
    """
    unlinked = []

    # Skip content inside existing wikilinks, code blocks, and frontmatter
    # Create a mask of protected regions
    protected = set()

    # Protect wikilinks
    for match in re.finditer(r'\[\[[^\]]+\]\]', content):
        for i in range(match.start(), match.end()):
            protected.add(i)

    # Protect code blocks
    for match in re.finditer(r'```[\s\S]*?```', content):
        for i in range(match.start(), match.end()):
            protected.add(i)

    # Protect inline code
    for match in re.finditer(r'`[^`]+`', content):
        for i in range(match.start(), match.end()):
            protected.add(i)

    # Protect frontmatter
    if content.startswith("---"):
        end_fm = content.find("---", 3)
        if end_fm != -1:
            for i in range(0, end_fm + 3):
                protected.add(i)

    # Protect URLs
    for match in re.finditer(r'https?://[^\s\)]+', content):
        for i in range(match.start(), match.end()):
            protected.add(i)

    for slug, variations in vocab.items():
        if slug.lower() in existing_links:
            continue

        for variation in variations:
            # Word boundary search (case-insensitive for most, exact for acronyms)
            if variation.isupper() and len(variation) <= 4:
                # Exact match for acronyms like ES, LLM, RAG
                pattern = r'\b' + re.escape(variation) + r'\b'
                flags = 0
            else:
                pattern = r'\b' + re.escape(variation) + r'\b'
                flags = re.IGNORECASE

            for match in re.finditer(pattern, content, flags):
                # Check if this position is protected
                if match.start() in protected:
                    continue

                original_text = match.group(0)

                # Determine display text
                if original_text.lower() == slug.lower():
                    suggested_link = f"[[{slug}]]"
                else:
                    suggested_link = f"[[{slug}|{original_text}]]"

                unlinked.append((original_text, slug, suggested_link, match.start()))

    # Remove duplicates (same slug appearing multiple times)
    seen_slugs = set()
    unique_unlinked = []
    for item in unlinked:
        if item[1] not in seen_slugs:
            seen_slugs.add(item[1])
            unique_unlinked.append(item[:3])  # Remove position from result

    return unique_unlinked


def apply_links(content: str, links_to_add: List[Tuple[str, str, str]]) -> str:
    """
    Apply wikilinks to content.
    Only links the FIRST occurrence of each term.
    """
    # Sort by length of original text (longest first) to avoid partial replacements
    links_to_add = sorted(links_to_add, key=lambda x: len(x[0]), reverse=True)

    for original_text, slug, suggested_link in links_to_add:
        # Build pattern that avoids already-linked content
        if original_text.isupper() and len(original_text) <= 4:
            pattern = r'(?<!\[\[)(?<!\|)\b' + re.escape(original_text) + r'\b(?!\]\])(?!\|)'
            flags = 0
        else:
            pattern = r'(?<!\[\[)(?<!\|)\b' + re.escape(original_text) + r'\b(?!\]\])(?!\|)'
            flags = re.IGNORECASE

        # Only replace first occurrence
        match = re.search(pattern, content, flags)
        if match:
            # Check we're not in a protected region
            pos = match.start()

            # Simple check: not inside frontmatter
            if content.startswith("---"):
                end_fm = content.find("---", 3)
                if end_fm != -1 and pos < end_fm:
                    continue

            # Simple check: not inside code block (rough heuristic)
            before = content[:pos]
            if before.count("```") % 2 == 1:
                continue

            # Apply the replacement
            actual_text = match.group(0)
            if actual_text.lower() == slug.lower() or actual_text.lower() == slug.replace("-", " ").lower():
                replacement = f"[[{slug}|{actual_text}]]"
            else:
                replacement = f"[[{slug}|{actual_text}]]"

            content = content[:match.start()] + replacement + content[match.end():]

    return content


def process_file(file_path: Path, vocab: Dict[str, List[str]], dry_run: bool = False, verbose: bool = False) -> int:
    """
    Process a single wiki file.
    Returns number of links added.
    """
    content = file_path.read_text(encoding="utf-8")

    # Get the current file's slug to avoid self-linking
    current_slug = file_path.stem
    filtered_vocab = {k: v for k, v in vocab.items() if k != current_slug}

    existing_links = find_existing_links(content)
    unlinked = find_unlinked_mentions(content, filtered_vocab, existing_links)

    if not unlinked:
        return 0

    if verbose:
        rel_path = file_path.relative_to(WIKI_ROOT)
        print(f"\n{rel_path}:")
        for original, slug, link in unlinked:
            print(f"  '{original}' -> {link}")

    if not dry_run:
        new_content = apply_links(content, unlinked)
        if new_content != content:
            file_path.write_text(new_content, encoding="utf-8")

    return len(unlinked)


def main():
    parser = argparse.ArgumentParser(description="Add wikilinks to wiki pages")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--file", type=str, help="Process only a specific file (relative to wiki/)")
    args = parser.parse_args()

    print("Building vocabulary...")
    vocab = build_vocabulary()
    print(f"Found {len(vocab)} linkable pages")

    total_links = 0
    files_modified = 0

    if args.file:
        # Process single file
        file_path = WIKI_ROOT / args.file
        if file_path.exists():
            links = process_file(file_path, vocab, args.dry_run, args.verbose)
            if links > 0:
                total_links += links
                files_modified += 1
        else:
            print(f"File not found: {file_path}")
            return
    else:
        # Process all content folders
        for folder in CONTENT_FOLDERS:
            folder_path = WIKI_ROOT / folder
            if not folder_path.exists():
                continue

            for md_file in folder_path.rglob("*.md"):
                if md_file.name in SKIP_FILES:
                    continue
                if any(skip in md_file.parts for skip in SKIP_FOLDERS):
                    continue

                links = process_file(md_file, vocab, args.dry_run, args.verbose)
                if links > 0:
                    total_links += links
                    files_modified += 1

    action = "Would add" if args.dry_run else "Added"
    print(f"\n{action} {total_links} links across {files_modified} files")


if __name__ == "__main__":
    main()
