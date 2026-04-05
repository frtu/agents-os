#!/bin/bash
# Downloader wrapper script
# Usage: ./downloader.sh <url> [-a area] [-r]
#
# Examples:
#   ./downloader.sh https://example.com
#   ./downloader.sh https://docs.python.org/3/ -a python-docs
#   ./downloader.sh https://blog.example.com -a blog --download-resources

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Run the downloader using the installed console script
exec uv run downloader "$@"