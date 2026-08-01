#!/usr/bin/env python3
"""
Unified markdown normalization utility.

Provides three independent normalizers (imported from existing scripts):
1. normalize_markdown_images() - Converts Slack emoji and Zoom speaker images to plain text
2. normalize_whitespace() - Cleans up whitespace issues from Slack exports
3. normalize_whitespace_in_code_blocks() - Removes unnecessary blank lines in code blocks

Can be applied independently or sequentially.
"""

import re
import sys
from pathlib import Path
from typing import Callable, Optional

from normalize_image_links import normalize_markdown_images
from normalize_whitespaces import normalize_whitespace, normalize_whitespace_in_code_blocks


def process_file(
	filepath: Path,
	dry_run: bool = False,
	normalizers: Optional[list[Callable[[str], str]]] = None
) -> tuple[bool, int]:
	"""
	Process a single markdown file with specified normalizers.

	Args:
		filepath: Path to the markdown file
		dry_run: If True, don't write changes
		normalizers: List of normalization functions to apply sequentially

	Returns:
		(changed, num_replacements)
	"""
	if normalizers is None:
		normalizers = []

	try:
		original_content = filepath.read_text(encoding='utf-8')
		normalized_content = original_content

		for normalizer in normalizers:
			normalized_content = normalizer(normalized_content)

		if original_content == normalized_content:
			return False, 0

		# Count image patterns for summary
		slack_matches = len(re.findall(r'!\[(:[\w-]+:)\]|\[!\[(:[\w-]+:)\]', original_content))
		zoom_matches = len(re.findall(r'!\[Speaker \d+\]\(https?://[^)]*zoom*[^)]*\)', original_content))
		base64_matches = len(re.findall(r'!\[[^\]]*\]\(data:image/[^;]+;base64,[^)]+\)', original_content))
		num_replacements = slack_matches + zoom_matches + base64_matches

		if not dry_run:
			filepath.write_text(normalized_content, encoding='utf-8')
			print(f"✓ Updated {filepath} ({num_replacements} images normalized)")
		else:
			print(f"[DRY RUN] Would update {filepath} ({num_replacements} images)")

		return True, num_replacements

	except Exception as e:
		print(f"✗ Error processing {filepath}: {e}", file=sys.stderr)
		return False, 0


def main():
	import argparse

	parser = argparse.ArgumentParser(
		description='Normalize markdown: images, whitespace, and code blocks',
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog="""
Examples:
  # Normalize images only
  %(prog)s --images /path/to/file.md

  # Normalize whitespace only
  %(prog)s --whitespace /path/to/file.md

  # Clean code blocks only
  %(prog)s --code-blocks /path/to/file.md

  # Apply all normalizations sequentially (default)
  %(prog)s /path/to/file.md

  # Apply custom sequence
  %(prog)s --whitespace --code-blocks /path/to/file.md

  # Dry run
  %(prog)s --dry-run /path/to/file.md
		"""
	)

	parser.add_argument(
		'files',
		nargs='+',
		type=Path,
		help='Markdown file(s) to process'
	)

	parser.add_argument(
		'--images',
		action='store_true',
		help='Normalize Slack emoji and Zoom speaker images'
	)

	parser.add_argument(
		'--whitespace',
		action='store_true',
		help='Normalize whitespace (collapse blank lines, trim trailing spaces)'
	)

	parser.add_argument(
		'--code-blocks',
		action='store_true',
		help='Remove blank lines inside code blocks'
	)

	parser.add_argument(
		'--dry-run',
		action='store_true',
		help='Show what would be changed without modifying files'
	)

	args = parser.parse_args()

	# If no normalizers specified, apply all three
	if not (args.images or args.whitespace or args.code_blocks):
		args.images = True
		args.whitespace = True
		args.code_blocks = True

	# Build list of normalizers in order
	normalizers = []
	if args.images:
		normalizers.append(normalize_markdown_images)
	if args.whitespace:
		normalizers.append(normalize_whitespace)
	if args.code_blocks:
		normalizers.append(normalize_whitespace_in_code_blocks)

	total_files = 0
	total_changed = 0
	total_replacements = 0

	for filepath in args.files:
		if not filepath.exists():
			print(f"✗ File not found: {filepath}", file=sys.stderr)
			continue

		if not filepath.is_file():
			print(f"✗ Not a file: {filepath}", file=sys.stderr)
			continue

		total_files += 1
		changed, num_replacements = process_file(filepath, args.dry_run, normalizers)

		if changed:
			total_changed += 1
			total_replacements += num_replacements

	print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary: {total_changed}/{total_files} files modified, {total_replacements} images normalized")

	return 0 if total_files > 0 else 1


if __name__ == '__main__':
	sys.exit(main())
